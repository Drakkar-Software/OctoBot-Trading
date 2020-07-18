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
from octobot_trading.orders.states.close_order_state import CloseOrderState


class CancelOrderState(OrderState):
    def __init__(self, order, is_from_exchange_data):
        super().__init__(order, is_from_exchange_data)
        self.state = OrderStates.CANCELING if not self.order.is_simulated else OrderStates.CANCELED

    def is_pending(self) -> bool:
        return self.state is OrderStates.CANCELING

    def is_closed(self) -> bool:
        return self.state is OrderStates.CANCELED

    def is_canceled(self) -> bool:
        return self.state is OrderStates.CANCELED

    async def on_order_refresh_successful(self):
        """
        TODO Verify the order is properly canceled
        """

    async def terminate(self):
        """
        Replace the order state by a close state
        """
        self.order.state = CloseOrderState(self.order,
                                           is_from_exchange_data=self.is_from_exchange_data,
                                           force_close=True)
        await self.order.state.initialize()
