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
        self.state = OrderStates.OPEN if is_from_exchange_data else OrderStates.OPENING

    async def synchronize(self) -> None:
        """
        TODO Should ask exchange if the order is properly created and still OrderStatus.OPEN
        """
        async def on_sync_succeed():
            pass
        await self._synchronize_order_with_exchange(on_sync_succeed)

    async def terminate(self):
        # Should be replaced by a FillOrderState or a CancelOrderState
        pass

    def is_pending(self) -> bool:
        return self.state is OrderStates.OPENING
