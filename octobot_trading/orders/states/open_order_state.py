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
from octobot_trading.orders.order_state import OrderState


class OpenOrderState(OrderState):
    def __init__(self, order, is_from_exchange_data):
        super().__init__(order, is_from_exchange_data)
        self.state = OrderStates.OPEN if is_from_exchange_data or self.order.is_simulated else OrderStates.OPENING

    async def on_order_refresh_successful(self):
        """
        TODO Verify the order is properly created and still OrderStatus.OPEN
        """

    async def terminate(self):
        """
        Should wait for being replaced by a FillOrderState or a CancelOrderState
        """

    def is_pending(self) -> bool:
        return self.state is OrderStates.OPENING
