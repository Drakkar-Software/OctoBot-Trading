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
import octobot_trading.constants as constants
import octobot_trading.personal_data.orders.order as order_class


class LimitOrder(order_class.Order):
    def __init__(self, trader, side=enums.TradeOrderSide.BUY):
        super().__init__(trader, side)
        self.limit_price_hit_event = None
        self.wait_for_hit_event_task = None
        self.trigger_above = self.side is enums.TradeOrderSide.SELL
        self.allow_instant_fill = True

    async def update_order_status(self, force_refresh=False):
        if self.limit_price_hit_event is None:
            self._create_hit_event(self.creation_time)

        if self.wait_for_hit_event_task is None and self.limit_price_hit_event is not None:
            if self.limit_price_hit_event.is_set():
                # order should be filled instantly
                await self.on_fill(force_fill=True)
            else:
                # order will be filled when conditions are met
                self._create_hit_task()

    def _on_origin_price_change(self, previous_price, price_time):
        if previous_price is not constants.ZERO:
            # no need to reset events if previous price was 0 (unset)
            self._reset_events(price_time)

    def _create_hit_event(self, price_time):
        self.limit_price_hit_event = self.exchange_manager.exchange_symbols_data.\
            get_exchange_symbol_data(self.symbol).price_events_manager.\
            new_event(self.origin_price, price_time, self.trigger_above, self.allow_instant_fill)

    def _create_hit_task(self):
        self.wait_for_hit_event_task = asyncio.create_task(self.wait_for_price_hit())

    def _reset_events(self, price_time):
        """
        Reset events and tasks
        """
        self._clear_event_and_tasks()
        self._create_hit_event(price_time)
        self._create_hit_task()

    def _clear_event_and_tasks(self):
        if self.wait_for_hit_event_task is not None:
            if not self.limit_price_hit_event.is_set():
                self.wait_for_hit_event_task.cancel()
            self.wait_for_hit_event_task = None
        if self.limit_price_hit_event is not None:
            self.exchange_manager.exchange_symbols_data. \
                get_exchange_symbol_data(self.symbol).price_events_manager.remove_event(self.limit_price_hit_event)

    async def wait_for_price_hit(self):
        await asyncio.wait_for(self.limit_price_hit_event.wait(), timeout=None)
        await self.on_fill()

    def _filled_maker_or_taker(self):
        return enums.ExchangeConstantsMarketPropertyColumns.MAKER.value

    def on_fill_actions(self):
        self.taker_or_maker = self._filled_maker_or_taker()
        self.filled_price = self.origin_price
        self.filled_quantity = self.origin_quantity
        self._update_total_cost()
        order_class.Order.on_fill_actions(self)

    def clear(self):
        self._clear_event_and_tasks()
        order_class.Order.clear(self)
