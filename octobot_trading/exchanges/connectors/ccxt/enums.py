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
import enum


class ExchangeConstantsCCXTColumns(enum.Enum):
    TIMESTAMP = "timestamp"
    DATETIME = "datetime"


class ExchangeConstantsMarketStatusCCXTColumns(enum.Enum):
    CONTRACT_SIZE = "contractSize"


class ExchangePositionCCXTColumns(enum.Enum):
    CONTRACTS = "contracts"
    CONTRACT_SIZE = "contractSize"
    MARGIN_TYPE = "marginType"
    MARGIN_MODE = "marginMode"
    LEVERAGE = "leverage"
    SYMBOL = "symbol"
    COLLATERAL = "collateral"
    INITIAL_MARGIN = "initialMargin"
    INITIAL_MARGIN_PERCENTAGE = "initialMarginPercentage"
    MAINTENANCE_MARGIN = "maintenanceMargin"
    MAINTENANCE_MARGIN_PERCENTAGE = "maintenanceMarginPercentage"
    NOTIONAL = "notional"
    MARGIN_RATIO = "marginRatio"
    UNREALISED_PNL = "unrealizedPnl"
    REALISED_PNL = "realizedPnl"
    LIQUIDATION_PRICE = "liquidationPrice"
    MARK_PRICE = "markPrice"
    ENTRY_PRICE = "entryPrice"
    TIMESTAMP = "timestamp"
    DATETIME = "datetime"
    PERCENTAGE = "percentage"
    SIDE = "side"
    HEDGED = "hedged"
    INFO = "info"


class ExchangeFundingCCXTColumns(enum.Enum):
    SYMBOL = "symbol"
    LAST_FUNDING_TIME = "lastFundingTime"
    FUNDING_RATE = "fundingRate"
    FUNDING_TIMESTAMP = "fundingTimestamp"
    NEXT_FUNDING_TIME = "nextFundingTime"
    NEXT_FUNDING_TIMESTAMP = "nextFundingTimestamp"
    PREDICTED_FUNDING_RATE = "predictedFundingRate"
    PREVIOUS_FUNDING_TIMESTAMP = "previousFundingTimestamp"
    PREVIOUS_FUNDING_RATE = "previousFundingRate"


class ExchangeLeverageTiersCCXTColumns(enum.Enum):
    TIER = "tier"
    CURRENCY = "currency"
    MIN_NOTIONAL = "minNotional"
    MAX_NOTIONAL = "maxNotional"
    MAINTENANCE_MARGIN_RATE = "maintenanceMarginRate"
    MAX_LEVERAGE = "maxLeverage"
    INFO = "info"


class ExchangeOrderCCXTColumns(enum.Enum):
    INFO = "info"
    ID = "id"
    TIMESTAMP = "timestamp"
    DATETIME = 'datetime'
    LAST_TRADE_TIMESTAMP = "lastTradeTimestamp"
    SYMBOL = "symbol"
    QUANTITY_CURRENCY = "quantityCurrency"
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
    TAKER_OR_MAKER = "takerOrMaker"
    REDUCE_ONLY = "reduceOnly"
    STOP_PRICE = "stopPrice"
    TRIGGER_PRICE = "triggerPrice"
    TRIGGER_ABOVE = "triggerAbove"
    TAG = "tag"
    MARGIN_MODE = "marginMode"


class ExchangeWrapperLibs(enum.Enum):
    ASYNC_CCXT = "async_ccxt"
    CCXT = "ccxt"


class ExchangeColumns(enum.Enum):
    WEBSITE = "www"
    URLS = "urls"
    API = "api"
    REST = "rest"
    WEBSOCKET = "ws"
    LOGO_URL = "logo"


class ExchangeMarginTypes(enum.Enum):
    ISOLATED = "isolated"
    CROSS = "cross"
