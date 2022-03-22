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
import octobot_trading.enums as enums
import octobot_trading.personal_data.orders.order_state as order_state


class PendingCreationOrderState(order_state.OrderState):

    def __init__(self, order, is_from_exchange_data):
        super().__init__(order, is_from_exchange_data)
        self.state = enums.States.PENDING_CREATION

    def is_created(self) -> bool:
        """
        :return: True if the Order is created
        """
        return False

    def is_open(self) -> bool:
        """
        :return: True if the Order is considered as open
        """
        return False

    async def update(self) -> None:
        # nothing to do as no actual order exists yet
        pass

    async def on_refresh_successful(self):
        # nothing to do as no actual order exists yet
        pass

    async def terminate(self):
        """
        Should wait for being replaced by an OpenOrderState or be cancelled
        """
        self.log_event_message(enums.StatesMessages.PENDING_CREATION)

    def is_pending(self) -> bool:
        return False
