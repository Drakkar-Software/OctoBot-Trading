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


class FillOrderState(OrderState):
    def __init__(self, order, is_from_exchange_data):
        super().__init__(order, is_from_exchange_data)
        self.state = OrderStates.FILLING \
            if not self.order.simulated and self.order.status not in [OrderStatus.FILLED, OrderStatus.CLOSED] \
            else OrderStates.FILLED

    async def initialize_impl(self, forced=False) -> None:
        if forced:
            self.state = OrderStates.FILLED
            self.order.status = OrderStatus.FILLED
        return await super().initialize_impl()

    def is_pending(self) -> bool:
        # TODO : Should also include OrderStates.PARTIALLY_FILLED ?
        return self.state is OrderStates.FILLING

    def is_filled(self) -> bool:
        # TODO : Should also include OrderStates.PARTIALLY_FILLED ?
        return self.state is OrderStates.FILLED

    async def on_order_refresh_successful(self):
        """
        Synchronize the filling status with the exchange
        can be a partially filled
        can also be still pending
        or be fully filled
        """
        if self.order.status in [OrderStatus.FILLED, OrderStatus.CLOSED]:
            self.state = OrderStates.FILLED
            await self.update()
        elif self.order.status is OrderStatus.PARTIALLY_FILLED:
            # TODO manage partially filled
            pass
        else:
            await create_order_state(self.order, is_from_exchange_data=True, ignore_states=[OrderStates.OPEN])

    async def terminate(self):
        """
        Perform order filling updates
        Replace the order state by a close state
        `force_close = True` because we know that the order is successfully filled.
        """
        try:
            self.log_order_event_message("filled")

            # call filling actions
            self.order.on_fill_actions()

            # set executed time
            self.order.executed_time = self.order.generate_executed_time()

            # Cancel linked orders
            for linked_order in self.order.linked_orders:
                await self.order.trader.cancel_order(linked_order, ignored_order=self.order)

            # compute trading fees
            try:
                self.order.fee = self.order.get_computed_fee()
            except KeyError:
                self.get_logger().error(f"Fail to compute trading fees for {self.order}.")

            # update portfolio with filled order
            async with self.order.exchange_manager.exchange_personal_data.get_order_portfolio(self.order).lock:
                await self.order.exchange_manager.exchange_personal_data.handle_portfolio_update_from_order(self.order)

            # notify order filled
            await self.order.exchange_manager.exchange_personal_data.handle_order_update_notification(self.order, False)

            # call order on_filled callback
            await self.order.on_filled()

            # set close state
            await self.order.on_close(force_close=True)  # TODO force ?
        except Exception as e:
            self.get_logger().exception(e, True, f"Fail to execute fill state termination : {e}.")
            raise
