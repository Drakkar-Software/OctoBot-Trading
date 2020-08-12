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
from octobot_trading.enums import ExchangeConstantsMarketPropertyColumns


class MarketOrder(Order):
    async def update_order_status(self, force_refresh=False):
        if not self.trader.simulate and (not self.is_synchronized_with_exchange or force_refresh):
            await self.default_exchange_update_order_status()
        # TODO for real orders : add post sync
        await self.on_fill()

    async def on_fill(self, force_fill=False, is_from_exchange_data=False):
        self.taker_or_maker = ExchangeConstantsMarketPropertyColumns.TAKER.value
        self.origin_price = self.created_last_price
        self.filled_price = self.created_last_price
        self.filled_quantity = self.origin_quantity
        self.total_cost = self.filled_price * self.filled_quantity
        await Order.on_fill(self, force_fill=force_fill, is_from_exchange_data=is_from_exchange_data)
