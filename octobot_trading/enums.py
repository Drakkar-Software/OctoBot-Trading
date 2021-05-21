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
import enum


class TradeOrderSide(enum.Enum):
    BUY = "buy"
    SELL = "sell"


class PositionSide(enum.Enum):
    LONG = "long"
    SHORT = "short"
    UNKNOWN = "unknown"


class TradeOrderType(enum.Enum):
    LIMIT = "limit"
    MARKET = "market"
    STOP_LOSS = "stop_loss"
    STOP_LOSS_LIMIT = "stop_loss_limit"
    TAKE_PROFIT = "take_profit"
    TAKE_PROFIT_LIMIT = "take_profit_limit"
    TRAILING_STOP = "trailing_stop"
    TRAILING_STOP_LIMIT = "trailing_stop_limit"
    LIMIT_MAKER = "limit_maker"  # LIMIT_MAKER is a limit order that is rejected if would be filled as taker
    UNKNOWN = "unknown"  # default value when the order type info is missing in the exchange data


class EvaluatorStates(enum.Enum):
    SHORT = "SHORT"
    VERY_SHORT = "VERY_SHORT"
    LONG = "LONG"
    VERY_LONG = "VERY_LONG"
    NEUTRAL = "NEUTRAL"


class OrderStatus(enum.Enum):
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    PENDING_CANCEL = "canceling"
    CLOSED = "closed"
    EXPIRED = "expired"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


class OrderStates(enum.Enum):
    OPENING = "opening"
    OPEN = "open"
    FILLING = "filling"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELING = "canceling"
    CANCELED = "canceled"
    CLOSING = "closing"
    CLOSED = "closed"
    REFRESHING = "refreshing"
    UNKNOWN = "unknown"


class PositionStatus(enum.Enum):
    LIQUIDATING = "liquidating"
    OPEN = "open"
    ADL = "auto_deleveraging"
    CLOSED = "closed"


class TraderOrderType(enum.Enum):
    BUY_MARKET = "buy_market"
    BUY_LIMIT = "buy_limit"
    STOP_LOSS = "stop_loss"
    STOP_LOSS_LIMIT = "stop_limit"
    SELL_MARKET = "sell_market"
    SELL_LIMIT = "sell_limit"
    TRAILING_STOP = "trailing_stop"
    TRAILING_STOP_LIMIT = "trailing_stop_limit"
    TAKE_PROFIT = "take_profit"
    TAKE_PROFIT_LIMIT = "take_profit_limit"
    UNKNOWN = "unknown"  # default value when the order type info is missing in the exchange data


class ExchangeConstantsCCXTColumns(enum.Enum):
    TIMESTAMP = "timestamp"
    DATETIME = "datetime"


class ExchangeConstantsFundingColumns(enum.Enum):
    SYMBOL = "symbol"
    LAST_FUNDING_TIME = "last_funding_time"
    FUNDING_RATE = "funding_rate"
    NEXT_FUNDING_TIME = "next_funding_time"


class ExchangeConstantsMarkPriceColumns(enum.Enum):
    SYMBOL = "symbol"
    TIMESTAMP = "timestamp"
    MARK_PRICE = "mark_price"


class ExchangeConstantsTickersColumns(enum.Enum):
    SYMBOL = "symbol"
    TIMESTAMP = "timestamp"
    DATETIME = "datetime"
    HIGH = "high"
    LOW = "low"
    BID = "bid"
    BID_VOLUME = "bidVolume"
    ASK = "ask"
    ASK_VOLUME = "askVolume"
    VWAP = "vwap"
    OPEN = "open"
    CLOSE = "close"
    LAST = "last"
    PREVIOUS_CLOSE = "previousClose"
    CHANGE = "change"
    PERCENTAGE = "percentage"
    AVERAGE = "average"
    BASE_VOLUME = "baseVolume"
    QUOTE_VOLUME = "quoteVolume"
    INFO = "info"


class ExchangeConstantsTickersInfoColumns(enum.Enum):
    SYMBOL = "symbol"
    PRICE_CHANGE = "priceChange"
    PRICE_CHANGE_PERCENT = "priceChangePercent"
    WEIGHTED_AVERAGE_PRICE = "weightedAvgPrice"
    PREVIOUS_CLOSE_PRICE = "prevClosePrice"
    LAST_PRICE = "lastPrice"
    LAST_QUANTITY = "lastQty"
    BID_PRICE = "bidPrice"
    BID_QUANTITY = "bidQty"
    ASK_PRICE = "askPrice"
    ASK_QUANTITY = "askQty"
    OPEN_PRICE = "openPrice"
    HIGH_PRICE = "highPrice"
    LOW_PRICE = "lowPrice"
    VOLUME = "volume"
    QUOTE_VOLUME = "quoteVolume"
    OPEN_TIME = "openTime"
    CLOSE_TIME = "closeTime"
    FIRST_ID = "firstId"
    LAST_ID = "lastId"
    COUNT = "count"


class ExchangeConstantsMiniTickerColumns(enum.Enum):
    SYMBOL = "symbol"
    OPEN_PRICE = "open_price"
    HIGH_PRICE = "high_price"
    LOW_PRICE = "low_price"
    CLOSE_PRICE = "close_price"
    VOLUME = "volume"
    TIMESTAMP = "timestamp"


class ExchangeConstantsMarketStatusColumns(enum.Enum):
    SYMBOL = "symbol"
    ID = "id"
    CURRENCY = "base"
    MARKET = "quote"
    ACTIVE = "active"
    PRECISION = "precision"  # number of decimal digits "after the dot"
    PRECISION_PRICE = "price"
    PRECISION_AMOUNT = "amount"
    PRECISION_COST = "cost"
    LIMITS = "limits"  # value limits when placing orders on this market
    LIMITS_AMOUNT = "amount"
    LIMITS_AMOUNT_MIN = "min"  # order amount should be > min
    LIMITS_AMOUNT_MAX = "max"  # order amount should be < max
    LIMITS_PRICE = "price"  # same min/max limits for the price of the order
    LIMITS_PRICE_MIN = "min"  # order price should be > min
    LIMITS_PRICE_MAX = "max"  # order price should be < max
    LIMITS_COST = "cost"  # same limits for order cost = price * amount
    LIMITS_COST_MIN = "min"  # order cost should be > min
    LIMITS_COST_MAX = "max"  # order cost should be < max
    INFO = "info"


class ExchangeConstantsMarketStatusInfoColumns(enum.Enum):
    # binance specific
    FILTERS = "filters"
    FILTER_TYPE = "filterType"
    PRICE_FILTER = "PRICE_FILTER"
    LOT_SIZE = "LOT_SIZE"
    MIN_PRICE = "minPrice"
    MAX_PRICE = "maxPrice"
    TICK_SIZE = "tickSize"
    MIN_QTY = "minQty"
    MAX_QTY = "maxQty"


class ExchangeConstantsOrderBookInfoColumns(enum.Enum):
    BIDS = "bids"
    ASKS = "asks"
    TIMESTAMP = "timestamp"
    DATETIME = "datetime"
    NONCE = "nonce"
    ORDER_ID = "order_id"
    PRICE = "price"
    SIZE = "size"
    SIDE = "side"


class ExchangeConstantsOrderBookTickerColumns(enum.Enum):
    BID_QUANTITY = "bid_quantity"
    BID_PRICE = "bid_price"
    ASK_QUANTITY = "ask_quantity"
    ASK_PRICE = "ask_price"
    SYMBOL = "symbol"
    TIMESTAMP = "timestamp"


class ExchangeConstantsOrderColumns(enum.Enum):
    INFO = "info"
    ID = "id"
    TIMESTAMP = "timestamp"
    DATETIME = 'datetime'
    LAST_TRADE_TIMESTAMP = "lastTradeTimestamp"
    SYMBOL = "symbol"
    TYPE = "type"
    SIDE = "side"
    PRICE = "price"
    AMOUNT = "amount"
    COST = "cost"
    AVERAGE = "average"
    FILLED = "filled"
    REMAINING = "remaining"
    STATUS = "status"
    FEE = "fee"
    TRADES = "trades"
    MAKER = "maker"
    TAKER = "taker"
    ORDER = "order"
    TAKERORMAKER = "takerOrMaker"
    REDUCE_ONLY = "reduceOnly"


class ExchangeConstantsPositionColumns(enum.Enum):
    ID = "id"
    TIMESTAMP = "timestamp"
    SYMBOL = "symbol"
    ENTRY_PRICE = "entry_price"
    MARK_PRICE = "mark_price"
    LIQUIDATION_PRICE = "liquidation_price"
    UNREALISED_PNL = "unrealised_pnl"
    REALISED_PNL = "realised_pnl"
    QUANTITY = "quantity"
    VALUE = "value"
    MARGIN = "margin"
    LEVERAGE = "leverage"
    STATUS = "status"
    SIDE = "side"


class ExchangeConstantsLiquidationColumns(enum.Enum):
    ID = "id"
    TIMESTAMP = "timestamp"
    SYMBOL = "symbol"
    PRICE = "price"
    QUANTITY = "quantity"
    SIDE = "side"


class ExchangeConstantsFeesColumns(enum.Enum):
    TYPE = "type"
    CURRENCY = "currency"
    RATE = "rate"
    COST = "cost"


class ExchangeConstantsMarketPropertyColumns(enum.Enum):
    TAKER = "taker"  # trading
    MAKER = "maker"  # trading
    FEE = "fee"  # withdraw


class FeePropertyColumns(enum.Enum):
    TYPE = "type"  # taker of maker
    CURRENCY = "currency"  # currency the fee is paid in
    RATE = "rate"  # multiplier applied to compute fee
    COST = "cost"  # fee amount


class AccountTypes(enum.Enum):
    CASH = "cash"
    MARGIN = "margin"
    FUTURE = "future"


class MarkPriceSources(enum.Enum):
    EXCHANGE_MARK_PRICE = "exchange_mark_price"
    RECENT_TRADE_AVERAGE = "recent_trade_average"
    TICKER_CLOSE_PRICE = "ticker_close_price"


class WebsocketFeeds(enum.Enum):
    L2_BOOK = 'l2_book'
    L3_BOOK = 'l3_book'
    BOOK_TICKER = 'book_ticker'
    BOOK_DELTA = 'book_delta'
    TRADES = 'trades'
    LIQUIDATIONS = 'liquidations'
    MINI_TICKER = 'mini_ticker'
    TICKER = 'ticker'
    CANDLE = 'candle'
    KLINE = 'kline'
    FUNDING = 'funding'
    MARK_PRICE = 'mark_price'
    MARKET_INFO = 'market_info'
    ORDERS = 'orders'
    FUTURES_INDEX = 'futures_index'
    OPEN_INTEREST = 'open_interest'
    PORTFOLIO = 'portfolio'
    POSITION = 'position'
    TRADE = 'trade'
    TRANSACTIONS = 'transactions'
    VOLUME = 'volume'
    UNSUPPORTED = 'unsupported'


class RestExchangePairsRefreshMaxThresholds(enum.Enum):
    FAST = 5
    MEDIUM = 10
    SLOW = 20


class MarginType(enum.Enum):
    CROSS = "cross"
    ISOLATE = "isolate"


class FutureContractType(enum.Enum):
    INVERSE_PERPETUAL = "inverse_perpetual"
    PERPETUAL = "perpetual"
    INVERSE_EXPIRABLE = "inverse_expirable"
    EXPIRABLE = "expirable"
