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

from octobot_trading.exchange_data cimport funding
from octobot_trading.exchange_data.funding cimport (
    FundingUpdaterSimulator,
    FundingUpdater,
    FundingManager,
    FundingProducer,
    FundingChannel,
)

from octobot_trading.exchange_data cimport kline
from octobot_trading.exchange_data.kline cimport (
    KlineUpdaterSimulator,
    KlineProducer,
    KlineChannel,
    KlineManager,
    KlineUpdater,
)

from octobot_trading.exchange_data cimport ohlcv
from octobot_trading.exchange_data.ohlcv cimport (
    CandlesManager,
    get_symbol_close_candles,
    get_symbol_open_candles,
    get_symbol_high_candles,
    get_symbol_low_candles,
    get_symbol_volume_candles,
    get_symbol_time_candles,
    OHLCVUpdaterSimulator,
    OHLCVProducer,
    OHLCVChannel,
    OHLCVUpdater,
)

from octobot_trading.exchange_data cimport order_book
from octobot_trading.exchange_data.order_book cimport (
    OrderBookUpdater,
    OrderBookProducer,
    OrderBookChannel,
    OrderBookTickerProducer,
    OrderBookTickerChannel,
    OrderBookManager,
    OrderBookUpdaterSimulator,
)

from octobot_trading.exchange_data cimport prices
from octobot_trading.exchange_data.prices cimport (
    MarkPriceUpdaterSimulator,
    MarkPriceProducer,
    MarkPriceChannel,
    PricesManager,
    calculate_mark_price_from_recent_trade_prices,
    MarkPriceUpdater,
    PriceEventsManager,
)

from octobot_trading.exchange_data cimport recent_trades
from octobot_trading.exchange_data.recent_trades cimport (
    RecentTradeProducer,
    RecentTradeChannel,
    LiquidationsProducer,
    LiquidationsChannel,
    RecentTradesManager,
    RecentTradeUpdater,
)

from octobot_trading.exchange_data cimport ticker
from octobot_trading.exchange_data.ticker cimport (
    TickerManager,
    TickerUpdater,
    TickerProducer,
    TickerChannel,
    MiniTickerProducer,
    MiniTickerChannel,
    TickerUpdaterSimulator,
)

from octobot_trading.exchange_data cimport contracts
from octobot_trading.exchange_data.contracts cimport (
    MarginContract,
    FutureContract,
)

from octobot_trading.exchange_data cimport exchange_symbol_data
from octobot_trading.exchange_data.exchange_symbol_data cimport (
    ExchangeSymbolData,
)
from octobot_trading.exchange_data cimport exchange_symbols_data
from octobot_trading.exchange_data.exchange_symbols_data cimport (
    ExchangeSymbolsData,
)

__all__ = [
    "FundingUpdaterSimulator",
    "FundingUpdater",
    "FundingManager",
    "FundingProducer",
    "FundingChannel",
    "KlineUpdaterSimulator",
    "KlineProducer",
    "KlineChannel",
    "KlineManager",
    "KlineUpdater",
    "CandlesManager",
    "get_symbol_close_candles",
    "get_symbol_open_candles",
    "get_symbol_high_candles",
    "get_symbol_low_candles",
    "get_symbol_volume_candles",
    "get_symbol_time_candles",
    "OHLCVUpdaterSimulator",
    "OHLCVProducer",
    "OHLCVChannel",
    "OHLCVUpdater",
    "OrderBookUpdater",
    "OrderBookProducer",
    "OrderBookChannel",
    "OrderBookTickerProducer",
    "OrderBookTickerChannel",
    "OrderBookManager",
    "OrderBookUpdaterSimulator",
    "MarkPriceUpdaterSimulator",
    "MarkPriceProducer",
    "MarkPriceChannel",
    "PricesManager",
    "calculate_mark_price_from_recent_trade_prices",
    "MarkPriceUpdater",
    "PriceEventsManager",
    "RecentTradeProducer",
    "RecentTradeChannel",
    "LiquidationsProducer",
    "LiquidationsChannel",
    "RecentTradesManager",
    "RecentTradeUpdater",
    "TickerManager",
    "TickerUpdater",
    "TickerProducer",
    "TickerChannel",
    "MiniTickerProducer",
    "MiniTickerChannel",
    "TickerUpdaterSimulator",
    "MarginContract",
    "FutureContract",
    "ExchangeSymbolsData",
    "ExchangeSymbolData",
]
