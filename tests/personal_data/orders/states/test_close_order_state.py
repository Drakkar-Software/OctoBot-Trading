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
import octobot_trading.personal_data as personal_data
from octobot_trading.enums import OrderStatus
from tests import event_loop
from tests.exchanges import simulated_trader, simulated_exchange_manager
from tests.personal_data.orders import sell_limit_order

import pytest

pytestmark = pytest.mark.asyncio


async def test_on_order_refresh_successful(sell_limit_order):
    sell_limit_order.status = OrderStatus.CLOSED
    sell_limit_order.exchange_manager.is_backtesting = True
    await sell_limit_order.initialize()
    assert isinstance(sell_limit_order.state, personal_data.CloseOrderState)
    await sell_limit_order.state.on_refresh_successful()
    assert sell_limit_order.is_closed()
    sell_limit_order.clear()
