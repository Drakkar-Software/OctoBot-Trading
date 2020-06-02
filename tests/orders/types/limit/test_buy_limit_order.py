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
import asyncio

import pytest

from octobot_trading.enums import TradeOrderType
from octobot_commons.asyncio_tools import wait_asyncio_next_cycle
from tests import event_loop
from tests.exchanges import simulated_trader, simulated_exchange_manager
from tests.orders import buy_limit_order

from tests.util.random_numbers import random_price, random_quantity, random_recent_trade, random_timestamp

pytestmark = pytest.mark.asyncio

DEFAULT_SYMBOL_ORDER = "BTC/USDT"


async def test_buy_limit_order_trigger(buy_limit_order):
    order_price = random_price()
    buy_limit_order.update(
        price=order_price,
        quantity=random_quantity(),
        symbol=DEFAULT_SYMBOL_ORDER,
        order_type=TradeOrderType.LIMIT,
    )
    buy_limit_order.exchange_manager.is_backtesting = True  # force update_order_status
    await buy_limit_order.initialize()
    price_events_manager = buy_limit_order.exchange_manager.exchange_symbols_data.get_exchange_symbol_data(
        DEFAULT_SYMBOL_ORDER).price_events_manager
    price_events_manager.handle_recent_trades(
        [random_recent_trade(price=random_price(min_value=order_price + 1),
                             timestamp=buy_limit_order.timestamp)])
    await wait_asyncio_next_cycle()
    assert not buy_limit_order.is_filled()
    price_events_manager.handle_recent_trades(
        [random_recent_trade(price=order_price,
                             timestamp=buy_limit_order.timestamp - 1)])
    await wait_asyncio_next_cycle()
    assert not buy_limit_order.is_filled()
    price_events_manager.handle_recent_trades([random_recent_trade(price=order_price,
                                                                   timestamp=buy_limit_order.timestamp)])

    await wait_asyncio_next_cycle()
    assert buy_limit_order.is_filled()
