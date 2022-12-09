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

from octobot_trading.exchanges.parser.util cimport Parser
from octobot_trading.exchanges.parser.positions_parser cimport PositionsParser
from octobot_trading.exchanges.parser.positions_parser_ccxt cimport CCXTPositionsParser
from octobot_trading.exchanges.parser.positions_parser_ccxt_generic cimport GenericCCXTPositionsParser
from octobot_trading.exchanges.parser.funding_rate_parser cimport FundingRateParser
from octobot_trading.exchanges.parser.funding_rate_parser_ccxt cimport CCXTFundingRateParser
from octobot_trading.exchanges.parser.funding_rate_parser_ccxt_generic cimport GenericCCXTFundingRateParser
from octobot_trading.exchanges.parser.orders_parser cimport OrdersParser
from octobot_trading.exchanges.parser.orders_parser_ccxt cimport CCXTOrdersParser
from octobot_trading.exchanges.parser.orders_parser_generic_ccxt cimport GenericCCXTOrdersParser
from octobot_trading.exchanges.parser.orders_parser_cryptofeed cimport CryptoFeedOrdersParser
from octobot_trading.exchanges.parser.trades_parser cimport TradesParser
from octobot_trading.exchanges.parser.trades_parser_ccxt cimport CCXTTradesParser
from octobot_trading.exchanges.parser.trades_parser_ccxt_generic cimport GenericCCXTTradesParser
from octobot_trading.exchanges.parser.trades_parser_cryptofeed cimport CryptoFeedTradesParser
from octobot_trading.exchanges.parser.ticker_parser cimport TickerParser, convert_ticker_to_mini_ticker
from octobot_trading.exchanges.parser.ticker_parser_ccxt cimport CCXTTickerParser
from octobot_trading.exchanges.parser.ticker_parser_ccxt_generic cimport GenericCCXTTickerParser
from octobot_trading.exchanges.parser.exchange_market_status_parser cimport (
    ExchangeMarketStatusParser,
    is_ms_valid,
)

__all__ = [
    "ExchangeMarketStatusParser",
    "is_ms_valid",
    "PositionsParser",
    "CCXTPositionsParser",
    "GenericCCXTPositionsParser",
    "TradesParser",
    "CCXTTradesParser",
    "GenericCCXTTradesParser",
    "CryptoFeedTradesParser",
    "convert_ticker_to_mini_ticker",
    "TickerParser",
    "CCXTTickerParser",
    "GenericCCXTTickerParser",
    "FundingRateParser",
    "CCXTFundingRateParser",
    "GenericCCXTFundingRateParser",
    "OrdersParser",
    "CCXTOrdersParser",
    "GenericCCXTOrdersParser",
    "CryptoFeedOrdersParser",
    "Parser"
]
