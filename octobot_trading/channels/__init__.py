#  Drakkar-Software OctoBot-Channels
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

from octobot_trading.channels.balance import BalanceChannel
from octobot_trading.channels.ohlcv import OHLCVChannel
from octobot_trading.channels.order_book import OrderBookChannel
from octobot_trading.channels.orders import OrdersChannel
from octobot_trading.channels.recent_trade import RecentTradeChannel
from octobot_trading.channels.ticker import TickerChannel

TICKER_CHANNEL = TickerChannel.get_name()
RECENT_TRADES_CHANNEL = RecentTradeChannel.get_name()
ORDER_BOOK_CHANNEL = OrderBookChannel.get_name()
OHLCV_CHANNEL = OHLCVChannel.get_name()
ORDERS_CHANNEL = OrdersChannel.get_name()
BALANCE_CHANNEL = BalanceChannel.get_name()
