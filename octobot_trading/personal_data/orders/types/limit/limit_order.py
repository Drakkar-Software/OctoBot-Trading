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

import octobot_trading.enums as enums
import octobot_trading.personal_data.orders.order as order_class


class LimitOrder(order_class.Order):
    def __init__(self, trader, side=enums.TradeOrderSide.BUY):
        super().__init__(trader, side)
        self.limit_price_hit_event = None
        self.wait_for_hit_event_task = None
        self.trigger_above = self.side is enums.TradeOrderSide.SELL

    async def update_order_status(self, force_refresh=False):
        if self.limit_price_hit_event is None:
            self.limit_price_hit_event = self.exchange_manager.exchange_symbols_data.\
                get_exchange_symbol_data(self.symbol).price_events_manager.\
                add_event(self.origin_price, self.creation_time, self.trigger_above)

        if self.wait_for_hit_event_task is None and self.limit_price_hit_event is not None:
            self.wait_for_hit_event_task = asyncio.create_task(self.wait_for_price_hit())

    async def wait_for_price_hit(self):
        await asyncio.wait_for(self.limit_price_hit_event.wait(), timeout=None)
        await self.on_fill()

    def on_fill_actions(self):
        self.taker_or_maker = enums.ExchangeConstantsMarketPropertyColumns.MAKER.value
        self.filled_price = self.origin_price
        self.filled_quantity = self.origin_quantity
        self.total_cost = self.filled_price * self.filled_quantity
        order_class.Order.on_fill_actions(self)

    def clear(self):
        if self.wait_for_hit_event_task is not None:
            if not self.limit_price_hit_event.is_set():
                self.wait_for_hit_event_task.cancel()
            self.wait_for_hit_event_task = None
        if self.limit_price_hit_event is not None:
            self.exchange_manager.exchange_symbols_data. \
                get_exchange_symbol_data(self.symbol).price_events_manager.remove_event(self.limit_price_hit_event)
        order_class.Order.clear(self)
