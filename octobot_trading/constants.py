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
import os
import typing

import octobot_trading.enums as enums
import octobot_commons.enums as commons_enums
import octobot_commons.constants as commons_constants
import octobot_commons.os_util as os_util

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
ALLOW_SIMULATED_ORDERS_INSTANT_FILL = os_util.parse_boolean_environment_var(
    "ALLOW_SIMULATED_ORDERS_INSTANT_FILL", "False"
)

# Order creation
ORDER_DATA_FETCHING_TIMEOUT = 5 * commons_constants.MINUTE_TO_SECONDS
CHAINED_ORDER_PRICE_FETCHING_TIMEOUT = 1    # should be instant or ignored
CHAINED_ORDERS_OUTDATED_PRICE_ALLOWANCE = decimal.Decimal("0.005")  # allows 0.5% outdated price error
# create instantly filled limit orders 0.5% beyond market
INSTANT_FILLED_LIMIT_ORDER_PRICE_DELTA = decimal.Decimal("0.005")
CREATED_ORDER_FORCED_UPDATE_PERIOD = 5

# Tentacles
TRADING_MODE_REQUIRED_STRATEGIES = "required_strategies"
TRADING_MODE_REQUIRED_STRATEGIES_MIN_COUNT = "required_strategies_min_count"
TENTACLES_TRADING_MODE_PATH = "Mode"
CONFIG_CANDLES_HISTORY_SIZE_TITLE = "Candles history size"
CONFIG_CANDLES_HISTORY_SIZE_KEY = CONFIG_CANDLES_HISTORY_SIZE_TITLE.replace(" ", "_")
CONFIG_BUY_ORDER_AMOUNT = "buy_order_amount"
CONFIG_SELL_ORDER_AMOUNT = "sell_order_amount"
CONFIG_LEVERAGE = "leverage"
TRADING_MODE_ACTIVITY_REASON = "reason"

# Exchange
DEFAULT_EXCHANGE_TIME_LAG = 10
DEFAULT_BACKTESTING_TIME_LAG = 0
INFINITE_MAX_HANDLED_PAIRS_WITH_TIMEFRAME = -1
DEFAULT_CANDLE_HISTORY_SIZE = 200
NO_DATA_LIMIT = -1
DEFAULT_FAILED_REQUEST_RETRY_TIME = 1
FAILED_NETWORK_REQUEST_RETRY_ATTEMPTS = 5
DEFAULT_REQUEST_TIMEOUT = int(os.getenv("DEFAULT_REQUEST_TIMEOUT", "20000"))    # default ccxt is 10s, use 20
ENABLE_EXCHANGE_HTTP_PROXY_FROM_ENV = os_util.parse_boolean_environment_var(
    "ENABLE_EXCHANGE_HTTP_PROXY_FROM_ENV", "True"
)
EXCHANGE_HTTP_PROXY_AUTHENTICATED_URL = os.getenv("EXCHANGE_HTTP_PROXY_AUTHENTICATED_URL")
EXCHANGE_HTTPS_PROXY_AUTHENTICATED_URL = os.getenv("EXCHANGE_HTTPS_PROXY_AUTHENTICATED_URL")
EXCHANGE_SOCKS_PROXY_AUTHENTICATED_URL = os.getenv("EXCHANGE_SOCKS_PROXY_AUTHENTICATED_URL")
ENABLE_CCXT_VERBOSE = os_util.parse_boolean_environment_var("ENABLE_CCXT_VERBOSE", "False")
ENABLE_CCXT_RATE_LIMIT = os_util.parse_boolean_environment_var("ENABLE_CCXT_RATE_LIMIT", "True")
ENABLE_CCXT_REQUESTS_COUNTER = os_util.parse_boolean_environment_var("ENABLE_CCXT_REQUESTS_COUNTER", "False")
CCXT_DEFAULT_CACHE_LIMIT = int(os.getenv("CCXT_DEFAULT_CACHE_LIMIT", "1000"))  # 1000: default ccxt value
CCXT_TRADES_CACHE_LIMIT = int(os.getenv("CCXT_TRADES_CACHE_LIMIT", str(CCXT_DEFAULT_CACHE_LIMIT)))
CCXT_ORDERS_CACHE_LIMIT = int(os.getenv("CCXT_ORDERS_CACHE_LIMIT", str(CCXT_DEFAULT_CACHE_LIMIT)))
CCXT_OHLCV_CACHE_LIMIT = int(os.getenv("CCXT_OHLCV_CACHE_LIMIT", str(CCXT_DEFAULT_CACHE_LIMIT)))
CCXT_WATCH_ORDER_BOOK_LIMIT = int(os.getenv("CCXT_WATCH_ORDER_BOOK_LIMIT", str(CCXT_DEFAULT_CACHE_LIMIT)))
THROTTLED_WS_UPDATES = float(os.getenv("THROTTLED_WS_UPDATES", "0.1"))  # avoid spamming CPU
MAX_CANDLES_IN_RAM = int(os.getenv("MAX_CANDLES_IN_RAM", "3000"))    # max candles per CandlesManager
STORAGE_ORIGIN_VALUE = "origin_value"
DISPLAY_TIME_FRAME = commons_enums.TimeFrames.ONE_HOUR
DEFAULT_SUBACCOUNT_ID = "default_subaccount_id"
DEFAULT_ACCOUNT_ID = "default_account_id"

# Storage
ENABLE_LIVE_CANDLES_STORAGE = os_util.parse_boolean_environment_var("ENABLE_LIVE_CANDLES_STORAGE", "False")
ENABLE_HISTORICAL_ORDERS_UPDATES_STORAGE = os_util.parse_boolean_environment_var("ENABLE_HISTORICAL_ORDERS_UPDATES_STORAGE", "False")
ENABLE_SIMULATED_ORDERS_STORAGE = os_util.parse_boolean_environment_var("ENABLE_SIMULATED_ORDERS_STORAGE", "False")
AUTH_UPDATE_DEBOUNCE_DURATION = float(os.getenv("AUTH_UPDATE_DEBOUNCE_DURATION", "10"))

# Decimal default values (decimals are immutable, can be stored as constant)
ZERO = decimal.Decimal(0)
ONE = decimal.Decimal(1)
ONE_HUNDRED = decimal.Decimal(100)
NaN = decimal.Decimal("nan")

# exchanges where test_get_historical_symbol_prices is successful can be listed here
FULL_CANDLE_HISTORY_EXCHANGES = [
    "ascendex",
    "binance",
    "bitfinex2",
    "bitstamp",
    "bybit",
    "bingx",
    "hollaex",
    "htx",
    "kucoin",
    "okcoin",
    "okx",
    "mexc",
    "coinbase",
    "binanceus",
    "bitmart",
    "bitmex",
]

DEFAULT_FUTURE_EXCHANGES = ["binanceusdm", "bybit"]
TESTED_EXCHANGES = [
    "binance",
    "kucoin",
    "okx",
] + sorted([
    "binanceus",
    "coinbase",
    "cryptocom",
    "htx",
    "bitget",
    "gateio",
    "ascendex",
    "bybit",
    "phemex",
    "hollaex",
    "mexc",
    "bingx",
    "coinex",
    "bitmart",
])
DEFAULT_FUTURE_EXCHANGES = sorted(["bybit"])
SIMULATOR_TESTED_EXCHANGES = sorted(["bitfinex2", "bithumb", "bitstamp", "bitmex",
                              "hitbtc", "kraken", "poloniex", "bitso", "ndax", "upbit",
                              "wavesexchange",])

# text content of errors due to exchange compliancy rules
# Warning: should never be a false positive
EXCHANGE_COMPLIANCY_ERRORS: typing.List[typing.Iterable[str]] = [
    # OKX ex: Trading of this pair or contract is restricted due to local compliance requirements
    ("restricted", "compliance"),
]

# text content of errors due to exchange local account permissions (ex: accounts from X country can't trade XYZ)
EXCHANGE_ACCOUNT_TRADED_SYMBOL_PERMISSION_ERRORS: typing.List[typing.Iterable[str]] = [
    # Binance ex: InvalidOrder binance {"code":-2010,"msg":"This symbol is not permitted for this account."}
    ("symbol", "not permitted", "for this account"),
]

CONFIG_DEFAULT_FEES = 0.001
CONFIG_DEFAULT_SIMULATOR_FEES = 0

DEFAULT_SYMBOL_LEVERAGE = ONE
DEFAULT_SYMBOL_MAX_LEVERAGE = ONE_HUNDRED
DEFAULT_SYMBOL_MARGIN_TYPE = enums.MarginType.ISOLATED
DEFAULT_SYMBOL_CONTRACT_TYPE = enums.FutureContractType.LINEAR_PERPETUAL
DEFAULT_SYMBOL_CONTRACT_SIZE = ONE
DEFAULT_SYMBOL_POSITION_MODE = enums.PositionMode.ONE_WAY
DEFAULT_SYMBOL_FUNDING_RATE = decimal.Decimal("0.00005")
DEFAULT_SYMBOL_MAINTENANCE_MARGIN_RATE = decimal.Decimal("0.01")

# used to force margin type update before positions init (if necessary)
FORCED_MARGIN_TYPE = enums.MarginType(os.getenv("FORCED_MARGIN_TYPE", enums.MarginType.ISOLATED.value))

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
INDIVIDUAL_ORDER_SYNC_TIMEOUT = 1 * commons_constants.MINUTE_TO_SECONDS
MAX_TRADES_COUNT = int(os.getenv("MAX_TRADES_COUNT", "10000"))    # larger values can use a large part of ram

# History
DEFAULT_SAVED_HISTORICAL_TIMEFRAMES = [commons_enums.TimeFrames.ONE_DAY]
HISTORICAL_CANDLES_FETCH_DEFAULT_TIMEOUT = 30

# 946742400 is 01/01/2000, if trade time is lower, there is an issue.
MINIMUM_VAL_TRADE_TIME = 946688400

# Internal
MODE_CHANNEL = "Mode"

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

ALWAYS_STARTED_REST_PRODUCER_CHANNELS = [
    TICKER_CHANNEL, # use to force mark price update when necessary: should always be reachable
]

FILL_ORDER_STATUS_SCOPE = [enums.OrderStatus.CLOSED,
                           enums.OrderStatus.FILLED,
                           enums.OrderStatus.PARTIALLY_FILLED]
CANCEL_ORDER_STATUS_SCOPE = [enums.OrderStatus.PENDING_CANCEL,
                             enums.OrderStatus.CANCELED,
                             enums.OrderStatus.EXPIRED,
                             enums.OrderStatus.REJECTED]

DEFAULT_INITIALIZATION_EVENT_TOPICS = [
    commons_enums.InitializationEventExchangeTopics.BALANCE,
    commons_enums.InitializationEventExchangeTopics.PROFITABILITY,
    commons_enums.InitializationEventExchangeTopics.ORDERS,
    commons_enums.InitializationEventExchangeTopics.TRADES,
    commons_enums.InitializationEventExchangeTopics.CANDLES,
    commons_enums.InitializationEventExchangeTopics.PRICE,
]

DEFAULT_FUTURES_INITIALIZATION_EVENT_TOPICS = DEFAULT_INITIALIZATION_EVENT_TOPICS + [
    commons_enums.InitializationEventExchangeTopics.POSITIONS,
    commons_enums.InitializationEventExchangeTopics.CONTRACTS,
    commons_enums.InitializationEventExchangeTopics.FUNDING,
]
