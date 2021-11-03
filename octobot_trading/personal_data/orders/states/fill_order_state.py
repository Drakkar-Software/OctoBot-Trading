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
import octobot_trading.constants as constants
import octobot_trading.enums as enums
import octobot_trading.personal_data.orders.order_state as order_state
import octobot_trading.personal_data.orders.states.order_state_factory as order_state_factory


class FillOrderState(order_state.OrderState):
    def __init__(self, order, is_from_exchange_data):
        super().__init__(order, is_from_exchange_data)
        self.state = enums.OrderStates.FILLING \
            if ((not self.order.simulated and not self.is_status_filled()) or self.is_status_pending()) \
            else enums.OrderStates.FILLED

    async def initialize_impl(self, forced=False) -> None:
        if forced:
            self.state = enums.OrderStates.FILLED
            self.order.status = enums.OrderStatus.FILLED
        return await super().initialize_impl()

    def is_pending(self) -> bool:
        return self.state is enums.OrderStates.FILLING

    def is_filled(self) -> bool:
        return self.state is enums.OrderStates.FILLED

    def is_status_pending(self) -> bool:
        return self.order.status is enums.OrderStatus.PARTIALLY_FILLED

    def is_status_filled(self) -> bool:
        return not self.is_status_pending() and self.order.status in constants.FILL_ORDER_STATUS_SCOPE

    async def on_refresh_successful(self):
        """
        Synchronize the filling status with the exchange
        can be a partially filled
        can also be still pending
        or be fully filled
        """
        if self.order.status is enums.OrderStatus.PARTIALLY_FILLED:
            # TODO manage partially filled
            await self.update()
        elif self.order.status in constants.FILL_ORDER_STATUS_SCOPE:
            self.state = enums.OrderStates.FILLED
            await self.update()
        else:
            await order_state_factory.create_order_state(self.order, is_from_exchange_data=True,
                                                         ignore_states=[enums.States.OPEN])

    async def terminate(self):
        """
        Perform order filling updates
        Replace the order state by a close state
        `force_close = True` because we know that the order is successfully filled.
        """
        try:
            self.log_event_message(enums.StatesMessages.FILLED)

            # call filling actions
            self.order.on_fill_actions()

            # set executed time
            self.order.executed_time = self.order.generate_executed_time()

            # Cancel linked orders
            for linked_order in self.order.linked_orders:
                await self.order.trader.cancel_order(linked_order, ignored_order=self.order)

            # compute trading fees
            try:
                if self.order.exchange_manager is not None:
                    self.order.fee = self.order.get_computed_fee()
            except KeyError:
                self.get_logger().error(f"Fail to compute trading fees for {self.order}.")

            # update portfolio with filled order and position if any
            async with self.order.exchange_manager.exchange_personal_data.get_order_portfolio(self.order).lock:
                await self.order.exchange_manager.exchange_personal_data.handle_portfolio_update_from_order(
                    self.order)

            # notify order filled
            await self.order.exchange_manager.exchange_personal_data.handle_order_update_notification(
                self.order, False)

            # call order on_filled callback
            await self.order.on_filled()

            # set close state
            await self.order.on_close(force_close=True)  # TODO force ?
        except Exception as e:
            self.get_logger().exception(e, True, f"Fail to execute fill state termination : {e}.")
            raise
