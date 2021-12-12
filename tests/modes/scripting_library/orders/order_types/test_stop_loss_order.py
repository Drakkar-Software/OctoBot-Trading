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
import mock

import octobot_trading.modes.scripting_library.orders.order_types.create_order as create_order
import octobot_trading.modes.scripting_library.orders.order_types.stop_loss_order as stop_loss_order

from tests import event_loop
from tests.modes.scripting_library import null_context


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_stop_loss(null_context):
    with mock.patch.object(create_order, "create_order_instance", mock.AsyncMock()) as create_order_instance:
        await stop_loss_order.stop_loss(null_context, "side", "symbol", "offset", "amount", "target_position",
                                        "one_cancels_the_other", "tag", "linked_to")
        create_order_instance.assert_called_once_with(
            null_context, side="side", symbol="symbol", order_amount="amount", order_target_position="target_position",
            order_type_name="stop_loss", order_offset="offset", one_cancels_the_other="one_cancels_the_other",
            tag="tag", linked_to="linked_to")
