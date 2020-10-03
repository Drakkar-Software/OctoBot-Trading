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
from octobot_trading.enums import OrderStatus
import pytest

pytestmark = pytest.mark.asyncio


async def test_on_order_refresh_successful(buy_limit_order):
    buy_limit_order.status = OrderStatus.FILLED
    buy_limit_order.exchange_manager.is_backtesting = True
    await buy_limit_order.initialize()
    await buy_limit_order.state.on_order_refresh_successful()
    assert buy_limit_order.is_closed()
    buy_limit_order.clear()
