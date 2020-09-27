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

from octobot_trading import constants
from octobot_trading import enums

from octobot_trading.constants import (BALANCE_CHANNEL,
                                       BALANCE_PROFITABILITY_CHANNEL,
                                       CCXT_INFO, CONFIG_DEFAULT_FEES,
                                       CONFIG_DEFAULT_SIMULATOR_FEES,
                                       CONFIG_EXCHANGES,
                                       CONFIG_EXCHANGE_ENCRYPTED_VALUES,
                                       CONFIG_EXCHANGE_FUTURE,
                                       CONFIG_EXCHANGE_KEY,
                                       CONFIG_EXCHANGE_MARGIN,
                                       CONFIG_EXCHANGE_PASSWORD,
                                       CONFIG_EXCHANGE_REST_ONLY,
                                       CONFIG_EXCHANGE_SANDBOXED,
                                       CONFIG_EXCHANGE_SECRET,
                                       CONFIG_EXCHANGE_SPOT,
                                       CONFIG_EXCHANGE_WEB_SOCKET,
                                       CONFIG_PORTFOLIO_FREE,
                                       CONFIG_PORTFOLIO_INFO,
                                       CONFIG_PORTFOLIO_MARGIN,
                                       CONFIG_PORTFOLIO_TOTAL,
                                       CONFIG_PORTFOLIO_USED, CONFIG_SIMULATOR,
                                       CONFIG_SIMULATOR_FEES,
                                       CONFIG_SIMULATOR_FEES_MAKER,
                                       CONFIG_SIMULATOR_FEES_TAKER,
                                       CONFIG_SIMULATOR_FEES_WITHDRAW,
                                       CONFIG_STARTING_PORTFOLIO,
                                       CONFIG_TRADER,
                                       CONFIG_TRADER_REFERENCE_MARKET,
                                       CONFIG_TRADER_RISK,
                                       CONFIG_TRADER_RISK_MAX,
                                       CONFIG_TRADER_RISK_MIN, CONFIG_TRADING,
                                       CURRENCY_DEFAULT_MAX_PRICE_DIGITS,
                                       CURRENT_PORTFOLIO_STRING,
                                       DEFAULT_BACKTESTING_TIME_LAG,
                                       DEFAULT_EXCHANGE_TIME_LAG,
                                       DEFAULT_REFERENCE_MARKET,
                                       FUNDING_CHANNEL, KLINE_CHANNEL,
                                       LIQUIDATIONS_CHANNEL,
                                       MARK_PRICE_CHANNEL, MINI_TICKER_CHANNEL,
                                       MODE_CHANNEL, OHLCV_CHANNEL,
                                       ORDERS_CHANNEL, ORDER_BOOK_CHANNEL,
                                       ORDER_BOOK_TICKER_CHANNEL,
                                       ORDER_DATA_FETCHING_TIMEOUT,
                                       POSITIONS_CHANNEL, REAL_TRADER_STR,
                                       RECENT_TRADES_CHANNEL,
                                       SIMULATOR_CURRENT_PORTFOLIO,
                                       SIMULATOR_LAST_PRICES_TO_CHECK,
                                       SIMULATOR_TESTED_EXCHANGES,
                                       SIMULATOR_TRADER_STR,
                                       TENTACLES_TRADING_MODE_PATH,
                                       TESTED_EXCHANGES, TICKER_CHANNEL,
                                       TRADES_CHANNEL,
                                       TRADING_MODE_REQUIRED_STRATEGIES,
                                       TRADING_MODE_REQUIRED_STRATEGIES_MIN_COUNT,
                                       WEBSOCKET_FEEDS_TO_TRADING_CHANNELS,)
from octobot_trading.enums import (AccountTypes, EvaluatorStates,
                                   ExchangeConstantsFeesColumns,
                                   ExchangeConstantsFundingColumns,
                                   ExchangeConstantsLiquidationColumns,
                                   ExchangeConstantsMarkPriceColumns,
                                   ExchangeConstantsMarketPropertyColumns,
                                   ExchangeConstantsMarketStatusColumns,
                                   ExchangeConstantsMarketStatusInfoColumns,
                                   ExchangeConstantsMiniTickerColumns,
                                   ExchangeConstantsOrderBookInfoColumns,
                                   ExchangeConstantsOrderBookTickerColumns,
                                   ExchangeConstantsOrderColumns,
                                   ExchangeConstantsPositionColumns,
                                   ExchangeConstantsTickersColumns,
                                   ExchangeConstantsTickersInfoColumns,
                                   FeePropertyColumns, MarginType,
                                   MarkPriceSources, OrderStates, OrderStatus,
                                   PositionSide, PositionStatus,
                                   RestExchangePairsRefreshMaxThresholds,
                                   TradeOrderSide, TradeOrderType,
                                   TraderOrderType, WebsocketFeeds,)

from octobot_trading.channels import *
from octobot_trading.producers import *
