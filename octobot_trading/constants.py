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
#  License along with this library
import decimal

import octobot_trading.enums as enums
import octobot_commons.enums as commons_enums

# Strings
CURRENT_PORTFOLIO_STRING = "Current Portfolio :"
CONFIG_PORTFOLIO_FREE = "free"
CONFIG_PORTFOLIO_USED = "used"
CONFIG_PORTFOLIO_TOTAL = "total"
CONFIG_PORTFOLIO_MARGIN = "margin"
REAL_TRADER_STR = "[Real Trader] "
SIMULATOR_TRADER_STR = "[Simulator] "

# Trader
DEFAULT_REFERENCE_MARKET = "BTC"
CURRENCY_DEFAULT_MAX_PRICE_DIGITS = 8

# Order creation
ORDER_DATA_FETCHING_TIMEOUT = 60

# Tentacles
TRADING_MODE_REQUIRED_STRATEGIES = "required_strategies"
TRADING_MODE_REQUIRED_STRATEGIES_MIN_COUNT = "required_strategies_min_count"
TENTACLES_TRADING_MODE_PATH = "Mode"
CONFIG_CANDLES_HISTORY_SIZE_TITLE = "Candles history size"
CONFIG_CANDLES_HISTORY_SIZE_KEY = CONFIG_CANDLES_HISTORY_SIZE_TITLE.replace(" ", "_")

# Exchange
DEFAULT_EXCHANGE_TIME_LAG = 10
DEFAULT_BACKTESTING_TIME_LAG = 0
INFINITE_MAX_HANDLED_PAIRS_WITH_TIMEFRAME = -1
DEFAULT_CANDLE_HISTORY_SIZE = 200

# Decimal default values (decimals are immutable, can be stored as constant)
ZERO = decimal.Decimal(0)
ONE = decimal.Decimal(1)
ONE_HUNDRED = decimal.Decimal(100)
NaN = decimal.Decimal("nan")

FULL_CANDLE_HISTORY_EXCHANGES = ["bequant", "binance", "binanceus", "binanceusdm", "bitcoincom",
                                 "bitfinex", "bitfinex2", "bitmex", "idex", "bybit"]

TESTED_EXCHANGES = ["binance", "ftx", "okex", "gateio", "huobi", "ascendex", "kucoin", "coinbasepro"]
SIMULATOR_TESTED_EXCHANGES = ["bybit"]

CONFIG_DEFAULT_FEES = 0.001
CONFIG_DEFAULT_SIMULATOR_FEES = 0

DEFAULT_SYMBOL_LEVERAGE = ONE
DEFAULT_SYMBOL_MAX_LEVERAGE = ONE_HUNDRED
DEFAULT_SYMBOL_MARGIN_TYPE = enums.MarginType.ISOLATED
DEFAULT_SYMBOL_CONTRACT_TYPE = enums.FutureContractType.LINEAR_PERPETUAL
DEFAULT_SYMBOL_POSITION_MODE = enums.PositionMode.ONE_WAY
DEFAULT_SYMBOL_FUNDING_RATE = decimal.Decimal("0.00005")
DEFAULT_SYMBOL_MAINTENANCE_MARGIN_RATE = decimal.Decimal("0.01")

# API
API_LOGGER_TAG = "TradingApi"

# Channels
# Exchange public data
TICKER_CHANNEL = "Ticker"
MINI_TICKER_CHANNEL = "MiniTicker"
RECENT_TRADES_CHANNEL = "RecentTrade"
LIQUIDATIONS_CHANNEL = "Liquidations"
ORDER_BOOK_CHANNEL = "OrderBook"
ORDER_BOOK_TICKER_CHANNEL = "OrderBookTicker"
KLINE_CHANNEL = "Kline"
OHLCV_CHANNEL = "OHLCV"
MARK_PRICE_CHANNEL = "MarkPrice"
FUNDING_CHANNEL = "Funding"

# Exchange personal data
TRADES_CHANNEL = "Trades"
ORDERS_CHANNEL = "Orders"
BALANCE_CHANNEL = "Balance"
BALANCE_PROFITABILITY_CHANNEL = "BalanceProfitability"
POSITIONS_CHANNEL = "Positions"

# History
DEFAULT_SAVED_HISTORICAL_TIMEFRAMES = [commons_enums.TimeFrames.ONE_DAY]

# 946742400 is 01/01/2000, if trade time is lower, there is an issue.
MINIMUM_VAL_TRADE_TIME = 946688400

# Internal
MODE_CHANNEL = "Mode"

# CCXT library constants
CCXT_INFO = "info"

WEBSOCKET_FEEDS_TO_TRADING_CHANNELS = {
    TICKER_CHANNEL: [enums.WebsocketFeeds.TICKER],
    MINI_TICKER_CHANNEL: [enums.WebsocketFeeds.MINI_TICKER],
    RECENT_TRADES_CHANNEL: [enums.WebsocketFeeds.TRADES],
    LIQUIDATIONS_CHANNEL: [enums.WebsocketFeeds.LIQUIDATIONS],
    ORDER_BOOK_CHANNEL: [enums.WebsocketFeeds.L2_BOOK, enums.WebsocketFeeds.L3_BOOK],
    ORDER_BOOK_TICKER_CHANNEL: [enums.WebsocketFeeds.BOOK_TICKER],
    KLINE_CHANNEL: [enums.WebsocketFeeds.KLINE],
    OHLCV_CHANNEL: [enums.WebsocketFeeds.CANDLE],
    TRADES_CHANNEL: [enums.WebsocketFeeds.TRADE],
    ORDERS_CHANNEL: [enums.WebsocketFeeds.ORDERS],
    MARK_PRICE_CHANNEL: [enums.WebsocketFeeds.MARK_PRICE],
    BALANCE_CHANNEL: [enums.WebsocketFeeds.PORTFOLIO],
    POSITIONS_CHANNEL: [enums.WebsocketFeeds.POSITION],
    FUNDING_CHANNEL: [enums.WebsocketFeeds.FUNDING]
}

FILL_ORDER_STATUS_SCOPE = [enums.OrderStatus.CLOSED,
                           enums.OrderStatus.FILLED,
                           enums.OrderStatus.PARTIALLY_FILLED]
CANCEL_ORDER_STATUS_SCOPE = [enums.OrderStatus.PENDING_CANCEL,
                             enums.OrderStatus.CANCELED,
                             enums.OrderStatus.EXPIRED,
                             enums.OrderStatus.REJECTED]
