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


class CloseOrderState(OrderState):
    def __init__(self, order, is_from_exchange_data, force_close=False):
        super().__init__(order, is_from_exchange_data)
        self.state = OrderStates.CLOSED if is_from_exchange_data or force_close else OrderStates.CLOSING

    def is_pending(self) -> bool:
        return self.state is OrderStates.CLOSING

    def is_closed(self) -> bool:
        return self.state is OrderStates.CLOSED

    async def synchronize(self) -> None:
        # Should ask exchange if the order is properly closed
        pass

    async def terminate(self):
        # Should be create a Trade when fully closed
        pass
