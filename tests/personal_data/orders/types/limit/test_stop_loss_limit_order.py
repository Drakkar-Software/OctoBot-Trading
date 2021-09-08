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
import pytest

from octobot_commons.asyncio_tools import wait_asyncio_next_cycle
from octobot_trading.enums import TraderOrderType, TradeOrderSide
from tests.personal_data import DEFAULT_ORDER_SYMBOL, DEFAULT_SYMBOL_QUANTITY
from tests.test_utils.random_numbers import decimal_random_price, random_price, decimal_random_quantity, \
    random_recent_trade

from tests import event_loop
from tests.exchanges import simulated_trader, simulated_exchange_manager
from tests.personal_data.orders import stop_loss_limit_order

pytestmark = pytest.mark.asyncio


async def test_stop_loss_limit_order_trigger(stop_loss_limit_order):
    order_price = decimal_random_price()
    stop_loss_limit_order.limit_price = order_price - 10
    stop_loss_limit_order.update(
        price=order_price,
        quantity=decimal_random_quantity(max_value=DEFAULT_SYMBOL_QUANTITY / 10),
        symbol=DEFAULT_ORDER_SYMBOL,
        order_type=TraderOrderType.STOP_LOSS_LIMIT,
    )
    stop_loss_limit_order.exchange_manager.is_backtesting = True  # force update_order_status
    await stop_loss_limit_order.initialize()
    stop_loss_limit_order.exchange_manager.exchange_personal_data.orders_manager.upsert_order_instance(
        stop_loss_limit_order
    )
    price_events_manager = stop_loss_limit_order.exchange_manager.exchange_symbols_data.get_exchange_symbol_data(
        DEFAULT_ORDER_SYMBOL).price_events_manager
    price_events_manager.handle_recent_trades(
        [random_recent_trade(price=random_price(min_value=float(order_price + 1)),
                             timestamp=stop_loss_limit_order.timestamp)])
    await wait_asyncio_next_cycle()
    assert not stop_loss_limit_order.is_filled()
    price_events_manager.handle_recent_trades(
        [random_recent_trade(price=order_price,
                             timestamp=stop_loss_limit_order.timestamp - 1)])
    await wait_asyncio_next_cycle()
    assert not stop_loss_limit_order.is_filled()
    price_events_manager.handle_recent_trades([random_recent_trade(price=order_price,
                                                                   timestamp=stop_loss_limit_order.timestamp)])

    # wait for 2 cycles as secondary orders are created
    await wait_asyncio_next_cycle()
    await wait_asyncio_next_cycle()
    assert stop_loss_limit_order.is_filled()

    # TODO add test create artificial order
