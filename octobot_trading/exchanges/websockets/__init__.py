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
from octobot_trading.channels import TICKER_CHANNEL, RECENT_TRADES_CHANNEL, ORDER_BOOK_CHANNEL, KLINE_CHANNEL, \
    OHLCV_CHANNEL, TRADES_CHANNEL, ORDERS_CHANNEL, BALANCE_CHANNEL, POSITIONS_CHANNEL

from octobot_trading.exchanges.websockets.octobot_websocket import OctoBotWebSocketClient
from octobot_websockets.constants import Feeds

WEBSOCKET_FEEDS_TO_TRADING_CHANNELS = {
    TICKER_CHANNEL: [Feeds.TICKER],
    RECENT_TRADES_CHANNEL: [Feeds.TRADES],
    ORDER_BOOK_CHANNEL: [Feeds.L2_BOOK, Feeds.L3_BOOK],
    KLINE_CHANNEL: [Feeds.KLINE],
    OHLCV_CHANNEL: [Feeds.CANDLE],
    TRADES_CHANNEL: [Feeds.TRADE],
    ORDERS_CHANNEL: [Feeds.ORDERS],
    BALANCE_CHANNEL: [Feeds.PORTFOLIO],
    POSITIONS_CHANNEL: [Feeds.POSITION]
}
