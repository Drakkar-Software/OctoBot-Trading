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

import octobot_trading.personal_data
import octobot_trading.errors

from tests import event_loop
from tests.exchanges import simulated_trader, simulated_exchange_manager
from tests.personal_data.orders import buy_limit_order

pytestmark = pytest.mark.asyncio


async def test_constructor(buy_limit_order):
    # with normal order
    state = octobot_trading.personal_data.OrderState(buy_limit_order, True)
    assert state.order is buy_limit_order

    # with cleared order
    buy_limit_order.state = state
    buy_limit_order.clear()
    with pytest.raises(octobot_trading.errors.InvalidOrderState):
        octobot_trading.personal_data.OrderState(buy_limit_order, True)
