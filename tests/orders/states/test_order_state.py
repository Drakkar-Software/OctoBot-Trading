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
from octobot_trading.enums import OrderStates
from octobot_trading.orders.states.order_state_factory import create_order_state
from tests import event_loop
from tests.exchanges import simulated_trader, simulated_exchange_manager
from tests.orders import buy_limit_order

import os
import pytest
from mock import AsyncMock, patch

pytestmark = pytest.mark.asyncio


async def test_synchronize(buy_limit_order):
    buy_limit_order.exchange_manager.is_backtesting = True
    await buy_limit_order.initialize()
    state = buy_limit_order.state
    assert state is not None
    assert state.state is not OrderStates.REFRESHING
    if not os.getenv('CYTHON_IGNORE'):
        with patch.object(state, '_refresh_order_from_exchange', new=AsyncMock()) as mocked_refresh_order:
            await state.synchronize()
            # calls _refresh_order_from_exchange since state is not OrderStates.REFRESHING
            mocked_refresh_order.assert_called_once()
            mocked_refresh_order.reset_mock()
            state.state = OrderStates.REFRESHING
            await state.synchronize()
            # _refresh_order_from_exchange NOT called since state is OrderStates.REFRESHING
            mocked_refresh_order.assert_not_called()
