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

from octobot_trading.enums import TraderOrderType
from octobot_trading.orders.types.limit.buy_limit_order import BuyLimitOrder
from octobot_trading.orders.types.limit.take_profit_limit_order import TakeProfitLimitOrder
from octobot_trading.orders.types.limit.take_profit_order import TakeProfitOrder
from octobot_trading.orders.types.market.buy_market_order import BuyMarketOrder
from octobot_trading.orders.types.limit.sell_limit_order import SellLimitOrder
from octobot_trading.orders.types.market.sell_market_order import SellMarketOrder
from octobot_trading.orders.types.limit.stop_loss_limit_order import StopLossLimitOrder
from octobot_trading.orders.types.limit.stop_loss_order import StopLossOrder
from octobot_trading.orders.types.trailing.trailing_stop_order import TrailingStopOrder
from octobot_trading.orders.types.trailing.trailing_stop_limit_order import TrailingStopLimitOrder
from octobot_trading.orders.types.unknown_order import UnknownOrder

TraderOrderTypeClasses = {
    TraderOrderType.BUY_MARKET: BuyMarketOrder,
    TraderOrderType.BUY_LIMIT: BuyLimitOrder,
    TraderOrderType.TAKE_PROFIT: TakeProfitOrder,
    TraderOrderType.TAKE_PROFIT_LIMIT: TakeProfitLimitOrder,
    TraderOrderType.TRAILING_STOP: TrailingStopOrder,
    TraderOrderType.TRAILING_STOP_LIMIT: TrailingStopLimitOrder,
    TraderOrderType.STOP_LOSS: StopLossOrder,
    TraderOrderType.STOP_LOSS_LIMIT: StopLossLimitOrder,
    TraderOrderType.SELL_MARKET: SellMarketOrder,
    TraderOrderType.SELL_LIMIT: SellLimitOrder,
    TraderOrderType.UNKNOWN: UnknownOrder,
}
