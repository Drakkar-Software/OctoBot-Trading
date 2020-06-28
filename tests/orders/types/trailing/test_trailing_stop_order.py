#  Drakkar-Software OctoBot-Trading
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
from typing import Tuple

import pytest

from octobot_commons.asyncio_tools import wait_asyncio_next_cycle

from octobot_trading.data_manager.price_events_manager import PriceEventsManager
from octobot_trading.enums import TradeOrderType, TradeOrderSide, MarkPriceSources
from octobot_trading.orders.types import TrailingStopOrder
from tests import event_loop
from tests.exchanges import simulated_trader, simulated_exchange_manager
from tests.orders import trailing_stop_order

from tests.util.random_numbers import random_price, random_quantity, random_recent_trade

pytestmark = pytest.mark.asyncio

DEFAULT_SYMBOL_ORDER = "BTC/USDT"


async def test_trailing_stop_trigger(trailing_stop_order):
    trailing_stop_order, order_price, price_events_manager = await initialize_trailing_stop(trailing_stop_order)
    await trailing_stop_order.set_trailing_percent(10)
    max_trailing_hit_price = get_price_percent(order_price, trailing_stop_order.trailing_percent)

    # set mark price
    set_mark_price(trailing_stop_order, order_price)

    price_events_manager.handle_recent_trades(
        [random_recent_trade(price=random_price(min_value=max_trailing_hit_price, max_value=order_price - 1),
                             timestamp=trailing_stop_order.timestamp)])
    await wait_asyncio_next_cycle()
    assert not trailing_stop_order.is_filled()
    price_events_manager.handle_recent_trades(
        [random_recent_trade(price=order_price,
                             timestamp=trailing_stop_order.timestamp - 1)])
    await wait_asyncio_next_cycle()
    assert not trailing_stop_order.is_filled()
    price_events_manager.handle_recent_trades([random_recent_trade(price=order_price,
                                                                   timestamp=trailing_stop_order.timestamp)])

    await wait_asyncio_next_cycle()
    assert not trailing_stop_order.is_filled()
    price_events_manager.handle_recent_trades([random_recent_trade(price=max_trailing_hit_price,
                                                                   timestamp=trailing_stop_order.timestamp)])
    await wait_asyncio_next_cycle()
    assert trailing_stop_order.is_filled()


async def test_trailing_stop_with_new_price(trailing_stop_order):
    trailing_stop_order, order_price, price_events_manager = await initialize_trailing_stop(trailing_stop_order)
    await trailing_stop_order.set_trailing_percent(2)
    new_trailing_price = random_price(min_value=order_price + 1)

    # set mark price
    set_mark_price(trailing_stop_order, new_trailing_price)

    # move trailing price
    price_events_manager.handle_recent_trades(
        [random_recent_trade(price=new_trailing_price,
                             timestamp=trailing_stop_order.timestamp)])
    await wait_asyncio_next_cycle()
    assert not trailing_stop_order.is_filled()

    # test fill stop loss with new order price reference
    price_events_manager.handle_recent_trades(
        [random_recent_trade(price=get_price_percent(new_trailing_price, trailing_stop_order.trailing_percent),
                             timestamp=trailing_stop_order.timestamp)])
    await wait_asyncio_next_cycle()
    assert trailing_stop_order.is_filled()


async def test_trailing_stop_with_new_old_price(trailing_stop_order):
    trailing_stop_order, order_price, price_events_manager = await initialize_trailing_stop(trailing_stop_order)
    await trailing_stop_order.set_trailing_percent(5)
    new_trailing_price = random_price(min_value=order_price + 1)

    # set mark price
    set_mark_price(trailing_stop_order, new_trailing_price)

    # move trailing price
    price_events_manager.handle_recent_trades(
        [random_recent_trade(price=new_trailing_price,
                             timestamp=trailing_stop_order.timestamp)])
    await wait_asyncio_next_cycle()
    assert not trailing_stop_order.is_filled()

    # test fill stop loss with old price
    price_events_manager.handle_recent_trades(
        [random_recent_trade(price=get_price_percent(order_price, trailing_stop_order.trailing_percent),
                             timestamp=trailing_stop_order.timestamp)])
    await wait_asyncio_next_cycle()
    assert trailing_stop_order.is_filled()


async def test_trailing_stop_with_new_price_inversed(trailing_stop_order):
    trailing_stop_order, order_price, price_events_manager = await initialize_trailing_stop(trailing_stop_order)
    trailing_stop_order.side = TradeOrderSide.BUY
    await trailing_stop_order.set_trailing_percent(5)
    new_trailing_price = random_price(max_value=order_price - 1)

    # set mark price
    set_mark_price(trailing_stop_order, new_trailing_price)

    # move trailing price
    price_events_manager.handle_recent_trades(
        [random_recent_trade(price=new_trailing_price,
                             timestamp=trailing_stop_order.timestamp)])
    await wait_asyncio_next_cycle()
    assert not trailing_stop_order.is_filled()

    # test fill stop loss with new order price reference
    price_events_manager.handle_recent_trades(
        [random_recent_trade(price=get_price_percent(new_trailing_price, trailing_stop_order.trailing_percent,
                                                     selling_side=False),
                             timestamp=trailing_stop_order.timestamp)])
    await wait_asyncio_next_cycle()
    assert trailing_stop_order.is_filled()


async def initialize_trailing_stop(order) -> Tuple[TrailingStopOrder, float, PriceEventsManager]:
    order_price = random_price()
    order.update(
        price=order_price,
        quantity=random_quantity(),
        symbol=DEFAULT_SYMBOL_ORDER,
        order_type=TradeOrderType.TRAILING_STOP,
    )
    order.exchange_manager.is_backtesting = True  # force update_order_status
    await order.initialize()
    price_events_manager = order.exchange_manager.exchange_symbols_data.get_exchange_symbol_data(
        DEFAULT_SYMBOL_ORDER).price_events_manager
    order.exchange_manager.exchange_personal_data.orders_manager.upsert_order_instance(order)
    return order, order_price, price_events_manager


def get_price_percent(price, percent, selling_side=True):
    return price * (1 + (percent / 100) * (-1 if selling_side else 1))


def set_mark_price(order, mark_price):
    prices_manager = order.exchange_manager.exchange_symbols_data. \
        get_exchange_symbol_data(order.symbol).prices_manager
    prices_manager.set_mark_price(mark_price, MarkPriceSources.EXCHANGE_MARK_PRICE.value)
    prices_manager.mark_price_set_time = order.timestamp
