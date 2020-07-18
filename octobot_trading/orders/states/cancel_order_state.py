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
from octobot_trading.data.order import Order
from octobot_trading.enums import OrderStates, OrderStatus
from octobot_trading.orders.order_state import OrderState
from octobot_trading.orders.states.close_order_state import CloseOrderState


class CancelOrderState(OrderState):
    def __init__(self, order, is_from_exchange_data):
        super().__init__(order, is_from_exchange_data)
        self.state = OrderStates.CANCELING if not self.order.is_simulated else OrderStates.CANCELED

    def is_pending(self) -> bool:
        return self.state is OrderStates.CANCELING

    def is_closed(self) -> bool:
        return self.state is OrderStates.CANCELED

    def is_canceled(self) -> bool:
        return self.state is OrderStates.CANCELED

    async def initialize_impl(self, ignored_order: Order = None) -> None:
        # always cancel this order first to avoid infinite loop followed by deadlock
        self.order.cancel_order()
        for linked_order in self.order.linked_orders:
            if linked_order is not ignored_order:
                await self.order.trader.cancel_order(linked_order, ignored_order=ignored_order)

        await super().initialize_impl()

    async def on_order_refresh_successful(self):
        """
        Verify the order is properly canceled
        """
        if self.order.status is OrderStatus.CANCELED:
            self.state = OrderStates.CANCELED

    async def terminate(self):
        """
        Replace the order state by a close state
        `force_close = True` because we know that the order is successfully cancelled.
        """
        self.get_logger().info(f"{self.order.symbol} {self.order.get_name()} at {self.order.origin_price}"
                               f" (ID: {self.order.order_id}) cancelled on {self.order.exchange_manager.exchange_name}")

        self.order.state = CloseOrderState(self.order,
                                           is_from_exchange_data=self.is_from_exchange_data,
                                           force_close=True)
        await self.order.state.initialize()
