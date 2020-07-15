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


class CancelOrderState(OrderState):
    def __init__(self, order, is_from_exchange_data):
        super().__init__(order, is_from_exchange_data)
        self.state = OrderStates.CANCELING

    def is_pending(self) -> bool:
        return self.state is OrderStates.CANCELING

    def is_closed(self) -> bool:
        return self.state is OrderStates.CANCELED

    def is_canceled(self) -> bool:
        return self.state is OrderStates.CANCELED

    async def synchronize(self) -> None:
        # Should ask exchange if the order is properly canceled
        pass

    async def terminate(self):
        # Should be replaced by a CloseOrderState when completely canceled
        pass
