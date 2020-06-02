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
from octobot_trading.enums import TradeOrderSide, TraderOrderType
from octobot_trading.orders.types.limit.limit_order import LimitOrder


class StopLossLimitOrder(LimitOrder):
    def __init__(self, trader, side=TradeOrderSide.BUY):
        super().__init__(trader)
        self.side = side

    async def on_fill(self):
        await super().on_fill()
        await self.trader.create_artificial_order(TraderOrderType.SELL_LIMIT, self.symbol, self.origin_stop_price,
                                                  self.origin_quantity, self.origin_stop_price,
                                                  self.linked_portfolio)  # TODO change price management
