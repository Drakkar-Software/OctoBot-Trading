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
from octobot_trading.enums import TradeOrderSide, OrderStatus, ExchangeConstantsMarketPropertyColumns
from octobot_trading.data.order import Order


class SellMarketOrder(Order):
    def __init__(self, trader):
        super().__init__(trader)
        self.side = TradeOrderSide.SELL

    async def update_order_status(self, last_prices: list, simulated_time=False):
        if not self.trader.simulate:
            await self.default_exchange_update_order_status()
        else:
            # ONLY FOR SIMULATION
            self.taker_or_maker = ExchangeConstantsMarketPropertyColumns.TAKER.value
            self.status = OrderStatus.FILLED
            self.origin_price = self.created_last_price
            self.filled_price = self.created_last_price
            self.filled_quantity = self.origin_quantity
            self.total_cost = self.filled_price * self.filled_quantity
            self.fee = self.get_computed_fee()
            self.executed_time = self.generate_executed_time(simulated_time)
