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
from octobot_trading.enums import OrderStates, OrderStatus
from octobot_trading.orders.order_state import OrderState


class OpenOrderState(OrderState):
    def __init__(self, order, is_from_exchange_data):
        super().__init__(order, is_from_exchange_data)
        self.state = OrderStates.OPEN if is_from_exchange_data or self.order.simulated or self.order.is_self_managed() else OrderStates.OPENING

    def is_open(self) -> bool:
        """
        :return: True if the Order is considered as open
        """
        return not (self.is_pending() or self.is_refreshing())

    async def initialize_impl(self) -> None:
        # update the availability of the currency in the portfolio
        self.order.exchange_manager.exchange_personal_data.portfolio_manager.portfolio. \
            update_portfolio_available(self.order, is_new_order=True)

        await super().initialize_impl()

    async def on_order_refresh_successful(self):
        """
        Verify the order is properly created and still OrderStatus.OPEN
        """
        if self.order.status is OrderStatus.OPEN:
            self.state = OrderStates.OPEN
        else:
            # notify order channel than an order has been created even though it's already closed
            await self.order.exchange_manager.exchange_personal_data.handle_order_update_notification(self.order, True)

            # set close state
            await self.order.on_close(force_close=True)  # TODO force ?

    async def terminate(self):
        """
        Should wait for being replaced by a FillOrderState or a CancelOrderState
        """
        self.log_order_event_message("open")

        # notify order manager of a new open order
        await self.order.exchange_manager.exchange_personal_data.handle_order_instance_update(self.order)

    def is_pending(self) -> bool:
        return self.state is OrderStates.OPENING
