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
import asyncio
import octobot_commons.asyncio_tools as asyncio_tools

import octobot_trading.enums as enums
import octobot_trading.personal_data.orders.order as order_class


class MarketOrder(order_class.Order):
    async def update_order_status(self, force_refresh=False):
        if self.trader.simulate:
            asyncio.create_task(self.on_fill(force_fill=True))
            # In trading simulation wait for the next asyncio loop iteration to ensure this order status
            # is updated before leaving this method
            await asyncio_tools.wait_asyncio_next_cycle()

    def on_fill_actions(self):
        self.taker_or_maker = enums.ExchangeConstantsMarketPropertyColumns.TAKER.value
        self.origin_price = self.created_last_price
        self.filled_price = self.created_last_price
        self.filled_quantity = self.origin_quantity
        self.total_cost = self.filled_price * self.filled_quantity
        order_class.Order.on_fill_actions(self)
