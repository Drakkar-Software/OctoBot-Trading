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
from octobot_commons.logging.logging_util import get_logger

from octobot_trading.enums import OrderStates, OrderStatus
from octobot_trading.orders.order_state import OrderState
from octobot_trading.orders.states.close_order_state import CloseOrderState


class FillOrderState(OrderState):
    def __init__(self, order, is_from_exchange_data):
        super().__init__(order, is_from_exchange_data)
        self.state = OrderStates.FILLING if not self.order.is_simulated else OrderStates.FILLED

    def is_pending(self) -> bool:
        # TODO : Should also include OrderStates.PARTIALLY_FILLED ?
        return self.state is OrderStates.FILLING

    def is_filled(self) -> bool:
        # TODO : Should also include OrderStates.PARTIALLY_FILLED ?
        return self.state is OrderStates.FILLED

    def is_closed(self) -> bool:
        return self.state is OrderStates.FILLED

    async def on_order_refresh_successful(self):
        """
        Synchronize the filling status with the exchange
        can be a partially filled
        can also be still pending
        or be fully filled
        """
        if self.order.status is OrderStatus.FILLED:
            self.state = OrderStates.FILLED
            self.order.executed_time = self.order.generate_executed_time()

            # TODO compute order fees
            self.order.fee = self.order.get_computed_fee()

        # TODO manage partially filled

    async def terminate(self):
        """
        Perform order filling updates
        Replace the order state by a close state
        `force_close = True` because we know that the order is successfully filled.
        """
        try:
            self.get_logger().info(f"{self.order.symbol} {self.order.get_name()} at {self.order.origin_price}"
                                   f" (ID: {self.order.order_id}) filled on {self.order.exchange_manager.exchange_name}")

            # Cancel linked orders
            for linked_order in self.order.linked_orders:
                await self.order.trader.cancel_order(linked_order, ignored_order=self.order)

            # update portfolio with filled order
            async with self.order.exchange_manager.exchange_personal_data.get_order_portfolio(self.order).lock:
                await self.order.exchange_manager.exchange_personal_data.handle_portfolio_update_from_order(self.order)

            # notify order filled
            await self.order.exchange_manager.exchange_personal_data.handle_order_update_notification(self.order, True)

            # set close state
            self.order.state = CloseOrderState(self.order,
                                               is_from_exchange_data=self.is_from_exchange_data,
                                               force_close=True)  # TODO force ?
            await self.order.state.initialize()
        except Exception as e:
            get_logger(self.get_logger()).exception(e, True, f"Fail to execute fill complete action : {e}.")
