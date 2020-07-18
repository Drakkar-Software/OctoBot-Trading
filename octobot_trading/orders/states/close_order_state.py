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
from octobot_trading.trades.trade_factory import create_trade_from_order


class CloseOrderState(OrderState):
    def __init__(self, order, is_from_exchange_data, force_close=False):
        super().__init__(order, is_from_exchange_data)
        self.state = OrderStates.CLOSED if is_from_exchange_data or force_close or self.order.is_simulated \
            else OrderStates.CLOSING

    def is_pending(self) -> bool:
        return self.state is OrderStates.CLOSING

    def is_closed(self) -> bool:
        return self.state is OrderStates.CLOSED

    async def on_order_refresh_successful(self):
        """
        TODO Verify the order is properly closed
        """

    async def terminate(self):
        """
        Handle order to trade conversion
        """
        # add to trade history and notify
        await self.order.exchange_manager.exchange_personal_data.handle_trade_instance_update(
            create_trade_from_order(self.order))

        # notify order trade created
        await self.order.on_trade_creation()

        # remove order from open_orders
        self.order.exchange_manager.exchange_personal_data.orders_manager.remove_order_instance(self.order)
