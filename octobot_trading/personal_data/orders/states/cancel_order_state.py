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
import octobot_trading.constants as constants
import octobot_trading.personal_data.orders.order_state as order_state
import octobot_trading.personal_data.orders.states.order_state_factory as order_state_factory


class CancelOrderState(order_state.OrderState):
    def __init__(self, order, is_from_exchange_data):
        super().__init__(order, is_from_exchange_data)
        self.state = enums.OrderStates.CANCELING \
            if ((not self.order.simulated and not self.is_status_cancelled()) or self.is_status_pending()) \
            else enums.OrderStates.CANCELED

    async def initialize_impl(self, forced=False, ignored_order=None) -> None:
        if forced:
            self.state = enums.OrderStates.CANCELED
            self.order.status = enums.OrderStatus.CANCELED

        # always cancel this order first to avoid infinite loop followed by deadlock
        for linked_order in self.order.linked_orders:
            if linked_order is not ignored_order and linked_order.is_open():
                await self.order.trader.cancel_order(linked_order, ignored_order=ignored_order)

        await super().initialize_impl()

    def is_pending(self) -> bool:
        return self.state is enums.OrderStates.CANCELING

    def is_canceled(self) -> bool:
        return self.state is enums.OrderStates.CANCELED

    def is_status_pending(self) -> bool:
        return self.order.status is enums.OrderStatus.PENDING_CANCEL

    def is_status_cancelled(self) -> bool:
        return not self.is_status_pending() and self.order.status in constants.CANCEL_ORDER_STATUS_SCOPE

    async def on_refresh_successful(self):
        """
        Verify the order is properly canceled
        """
        if self.is_status_pending():
            # TODO manage pending cancel
            await self.update()
        elif self.order.status in constants.CANCEL_ORDER_STATUS_SCOPE:
            self.state = enums.OrderStates.CANCELED
            await self.update()
        else:
            await order_state_factory.create_order_state(self.order, is_from_exchange_data=True,
                                                         ignore_states=[enums.States.OPEN])

    async def terminate(self):
        """
        Replace the order state by a close state
        `force_close = True` because we know that the order is successfully cancelled.
        """
        try:
            self.log_event_message(enums.StatesMessages.CANCELLED)

            # set cancel time
            self.order.canceled_time = self.order.exchange_manager.exchange.get_exchange_current_time()

            # update portfolio after close
            async with self.order.exchange_manager.exchange_personal_data.get_order_portfolio(self.order).lock:
                await self.order.exchange_manager.exchange_personal_data.handle_portfolio_update_from_order(self.order,
                                                                                                            False)

            # notify order filled
            await self.order.exchange_manager.exchange_personal_data.handle_order_update_notification(self.order,
                                                                                                      False)

            # set close state
            await self.order.on_close(force_close=True)  # TODO force ?
        except Exception as e:
            self.get_logger().exception(e, True, f"Fail to execute cancel state termination : {e}.")
            raise
