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


class CancelOrderState(OrderState):
    def __init__(self, order, is_from_exchange_data):
        super().__init__(order, is_from_exchange_data)
        self.state = OrderStates.CANCELING if not self.order.simulated and \
                                              self.order.status is not OrderStatus.CANCELED else OrderStates.CANCELED

    async def initialize_impl(self, forced=False, ignored_order=None) -> None:
        if forced:
            self.state = OrderStates.CANCELED
            self.order.status = OrderStatus.CANCELED

        # always cancel this order first to avoid infinite loop followed by deadlock
        for linked_order in self.order.linked_orders:
            if linked_order is not ignored_order and linked_order.is_open():
                await self.order.trader.cancel_order(linked_order, ignored_order=ignored_order)

        await super().initialize_impl()

    def is_pending(self) -> bool:
        return self.state is OrderStates.CANCELING

    def is_canceled(self) -> bool:
        return self.state is OrderStates.CANCELED

    async def on_order_refresh_successful(self):
        """
        Verify the order is properly canceled
        """
        if self.order.status is OrderStatus.CANCELED:
            self.state = OrderStates.CANCELED
            await self.update()
        else:
            await create_order_state(self.order, is_from_exchange_data=True, ignore_states=[OrderStates.OPEN])

    async def terminate(self):
        """
        Replace the order state by a close state
        `force_close = True` because we know that the order is successfully cancelled.
        """
        try:
            self.log_order_event_message("cancelled")

            # set cancel time
            self.order.canceled_time = self.order.exchange_manager.exchange.get_exchange_current_time()

            # update portfolio after close
            async with self.order.exchange_manager.exchange_personal_data.get_order_portfolio(self.order).lock:
                await self.order.exchange_manager.exchange_personal_data.handle_portfolio_update_from_order(self.order)

            # notify order filled
            await self.order.exchange_manager.exchange_personal_data.handle_order_update_notification(self.order,
                                                                                                      False)

            # set close state
            await self.order.on_close(force_close=True)  # TODO force ?
        except Exception as e:
            self.get_logger().exception(e, True, f"Fail to execute cancel state termination : {e}.")
            raise
