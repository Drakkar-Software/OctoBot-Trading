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
from asyncio import wait_for

from octobot_trading.data.order import Order
from octobot_trading.enums import TradeOrderSide, OrderStatus, ExchangeConstantsMarketPropertyColumns


class LimitOrder(Order):
    def __init__(self, trader):
        super().__init__(trader)
        self.side = TradeOrderSide.BUY
        self.limit_price_hit_event = None
        self.wait_for_hit_event_task = None

    async def update_order_status(self, force_refresh=False):
        if not self.trader.simulate and (not self.is_synchronized_with_exchange or force_refresh):
            await self.default_exchange_update_order_status()

        if self.limit_price_hit_event is None:
            self.limit_price_hit_event = self.exchange_manager.exchange_symbols_data.\
                get_exchange_symbol_data(self.symbol).price_events_manager.\
                add_event(self.origin_price, self.creation_time, self.side == TradeOrderSide.SELL)

        if self.wait_for_hit_event_task is None and self.limit_price_hit_event is not None:
            self.wait_for_hit_event_task = asyncio.create_task(self.wait_for_price_hit())

    async def wait_for_price_hit(self):
        await wait_for(self.limit_price_hit_event.wait(), timeout=None)
        await self.perform_price_hit()

    async def perform_price_hit(self):
        self.taker_or_maker = ExchangeConstantsMarketPropertyColumns.MAKER.value
        self.status = OrderStatus.FILLED
        self.filled_price = self.origin_price
        self.filled_quantity = self.origin_quantity
        self.total_cost = self.filled_price * self.filled_quantity
        self.fee = self.get_computed_fee()
        self.executed_time = self.generate_executed_time()
        for order in self.linked_orders:
            await self.trader.cancel_order(order)
