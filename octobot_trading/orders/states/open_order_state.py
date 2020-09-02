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
from octobot_trading.orders.states.order_state_factory import create_order_state


class OpenOrderState(OrderState):
    def __init__(self, order, is_from_exchange_data):
        super().__init__(order, is_from_exchange_data)
        self.state = OrderStates.OPEN if is_from_exchange_data \
                                         or self.order.simulated \
                                         or self.order.is_self_managed() \
                                         or self.order.status is OrderStatus.OPEN \
            else OrderStates.OPENING

        self.has_terminated = False

    def is_open(self) -> bool:
        """
        :return: True if the Order is considered as open
        """
        return not (self.is_pending() or self.is_refreshing())

    async def initialize_impl(self, forced=False) -> None:
        if forced:
            self.state = OrderStates.OPEN

        # update the availability of the currency in the portfolio
        self.order.exchange_manager.exchange_personal_data.portfolio_manager.portfolio. \
            update_portfolio_available(self.order, is_new_order=True)

        return await super().initialize_impl()

    async def on_order_refresh_successful(self):
        """
        Verify the order is properly created and still OrderStatus.OPEN
        """
        # skip refresh process if the current order state is not the same as the one triggering this
        # on_order_refresh_successful to avoid synchronization issues (state already got refreshed by another mean)
        if self.state is self.order.state.state:
            if self.order.status is OrderStatus.OPEN:
                self.state = OrderStates.OPEN
                await self.update()
            else:
                if self.order.status is OrderStatus.CLOSED:
                    self.order.status = OrderStatus.FILLED
                    self.order.state = None
                await create_order_state(self.order, is_from_exchange_data=True)
        else:
            self.get_logger().debug(f"on_order_refresh_successful triggered from previous state "
                                    f"after state change on {self.order}")

    async def terminate(self):
        """
        Should wait for being replaced by a FillOrderState or a CancelOrderState
        """
        if not self.has_terminated:
            self.log_order_event_message("open")

            # notify order manager of a new open order
            await self.order.exchange_manager.exchange_personal_data.handle_order_instance_update(self.order,
                                                                                                  should_notify=True)
            self.has_terminated = True

    def is_pending(self) -> bool:
        return self.state is OrderStates.OPENING
