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

from octobot_commons.logging.logging_util import get_logger

from octobot_trading.data_manager.candles_manager import CandlesManager
from octobot_trading.data_manager.funding_manager import FundingManager
from octobot_trading.data_manager.kline_manager import KlineManager
from octobot_trading.data_manager.order_book_manager import OrderBookManager
from octobot_trading.data_manager.prices_manager import PricesManager
from octobot_trading.data_manager.recent_trades_manager import RecentTradesManager
from octobot_trading.data_manager.ticker_manager import TickerManager


class ExchangeSymbolData:
    MAX_ORDER_BOOK_ORDER_COUNT = 100
    MAX_RECENT_TRADES_COUNT = 100

    def __init__(self, exchange_manager, symbol):
        self.symbol = symbol
        self.exchange_manager = exchange_manager

        self.order_book_manager = OrderBookManager()
        self.prices_manager = PricesManager()
        self.recent_trades_manager = RecentTradesManager()
        self.ticker_manager = TickerManager()
        self.funding_manager = FundingManager() if self.exchange_manager.is_margin else None

        self.symbol_candles = {}
        self.symbol_klines = {}

        self.logger = get_logger(f"{self.__class__.__name__} - {self.symbol}")

    # candle functions
    async def handle_candles_update(self, time_frame, new_symbol_candles_data, replace_all=False, partial=False):
        try:
            symbol_candles = self.symbol_candles[time_frame]
        except KeyError:
            symbol_candles = CandlesManager()
            await symbol_candles.initialize()

            if replace_all:
                symbol_candles.replace_all_candles(new_symbol_candles_data)
            else:
                pass  # TODO ask exchange to init

            self.symbol_candles[time_frame] = symbol_candles
            return

        if partial:
            symbol_candles.add_old_and_new_candles(new_symbol_candles_data)
        elif replace_all:
            symbol_candles.replace_all_candles(new_symbol_candles_data)
        else:
            symbol_candles.add_new_candle(new_symbol_candles_data)

    def handle_recent_trade_update(self, recent_trades, replace_all=False, partial=False):
        if partial:
            # TODO check if initialized
            return self.recent_trades_manager.add_new_trades(recent_trades)
        elif replace_all:
            return self.recent_trades_manager.set_all_recent_trades(recent_trades)
        # TODO check if initialized

        # recent trades should be a dict
        return self.recent_trades_manager.add_recent_trade(recent_trades)

    def handle_mark_price_update(self, mark_price):
        self.prices_manager.set_mark_price(mark_price)

    def handle_order_book_update(self, asks, bids, is_delta=False):
        if is_delta:
            # TODO check if initialized
            self.order_book_manager.order_book_delta_update(asks, bids)
        else:
            self.order_book_manager.order_book_update(asks, bids)

    def handle_ticker_update(self, ticker):
        self.ticker_manager.ticker_update(ticker)

    async def handle_kline_update(self, time_frame, kline):
        try:
            symbol_klines = self.symbol_klines[time_frame]
        except KeyError:
            symbol_klines = KlineManager()
            try:
                await symbol_klines.initialize()
                symbol_klines.kline_update(kline)
                self.symbol_klines[time_frame] = symbol_klines
            except KeyError:
                self.logger.warning("Can't initialize kline manager : missing required candles data.")
                return

        symbol_klines.kline_update(kline)

    async def handle_funding_update(self, funding_rate, next_funding_time, timestamp):
        if self.funding_manager:
            self.funding_manager.funding_update(funding_rate, next_funding_time, timestamp)
