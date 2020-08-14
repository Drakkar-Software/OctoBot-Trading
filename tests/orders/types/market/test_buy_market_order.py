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
from octobot_trading.enums import TraderOrderType
from tests import event_loop
from tests.exchanges import simulated_trader, simulated_exchange_manager
from tests.orders import buy_market_order
from tests.util.random_numbers import random_price, random_quantity, random_recent_trade

pytestmark = pytest.mark.asyncio

DEFAULT_SYMBOL_ORDER = "BTC/USDT"


async def test_buy_market_order_trigger(buy_market_order):
    order_price = random_price()
    buy_market_order.update(
        price=order_price,
        quantity=random_quantity(),
        symbol=DEFAULT_SYMBOL_ORDER,
        order_type=TraderOrderType.BUY_MARKET,
    )
    buy_market_order.exchange_manager.is_backtesting = True  # force update_order_status
    await buy_market_order.initialize()
    assert buy_market_order.is_filled()
