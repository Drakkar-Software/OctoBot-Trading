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

import time

import numpy as np
from octobot_commons.enums import PriceIndexes, TimeFramesMinutes

from octobot_commons.logging.logging_util import get_logger

from octobot_trading.data_manager.candles_manager import CandlesManager
from octobot_trading.data_manager.kline_manager import KlineManager
from octobot_trading.data_manager.order_book_manager import OrderBookManager
from octobot_trading.data_manager.recent_trades_manager import RecentTradesManager
from octobot_trading.data_manager.ticker_manager import TickerManager


class ExchangeSymbolData:
    MAX_ORDER_BOOK_ORDER_COUNT = 100
    MAX_RECENT_TRADES_COUNT = 100

    def __init__(self, symbol):
        self.symbol = symbol

        self.order_book_manager = OrderBookManager()
        self.recent_trades_manager = RecentTradesManager()
        self.ticker_manager = TickerManager()

        self.symbol_candles = {}
        self.symbol_klines = {}

        self.are_recent_trades_initialized = False  # TODO to be removed
        self.is_order_book_initialized = False  # TODO to be removed
        self.is_price_ticker_initialized = False  # TODO to be removed

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
            self.recent_trades_manager.add_new_trades(recent_trades)
        elif replace_all:
            self.recent_trades_manager.set_all_recent_trades(recent_trades)
        else:
            # TODO check if initialized
            self.recent_trades_manager.add_recent_trade(recent_trades[-1])

    def handle_order_book_update(self, asks, bids, is_delta=False):
        if is_delta:
            # TODO check if initialized
            self.order_book_manager.order_book_delta_update(asks, bids)
        else:
            self.order_book_manager.order_book_update(asks, bids)

    def handle_ticker_update(self, ticker):
        self.ticker_manager.ticker_update(ticker)

    async def handle_kline_update(self, time_frame, kline, should_reset=False):
        try:
            symbol_klines = self.symbol_klines[time_frame]
        except KeyError:
            symbol_klines = KlineManager()
            try:
                await symbol_klines.initialize()
                symbol_klines.reset_kline(kline)
                self.symbol_klines[time_frame] = symbol_klines
            except KeyError:
                self.logger.warning("Can't initialize kline manager : missing required candles data.")
                return

        if should_reset:
            symbol_klines.reset_kline(kline)

        symbol_klines.kline_update(kline)

    def handle_kline_reset(self, last_candle, time_frame):
        if time_frame in self.symbol_klines:
            self.symbol_klines[time_frame].reset_kline(last_candle)

    '''
    Called by non-trade classes
    '''

    # candle functions
    def get_candle_data(self, time_frame):
        if time_frame in self.symbol_candles:
            return self.symbol_candles[time_frame]
        elif time_frame is None:
            return self.symbol_candles[next(iter(self.symbol_candles))]
        return None

    def get_available_time_frames(self):
        return self.symbol_candles.keys()

    # ticker functions
    def get_symbol_ticker(self):
        return self.ticker_manager  # TODO

    # order book functions
    def get_symbol_order_book(self):
        return self.order_book_manager  # TODO

    # recent trade functions
    def get_symbol_recent_trades(self, limit=None):
        if limit:
            return self.recent_trades_manager[-limit:]  # TODO
        else:
            return self.recent_trades_manager  # TODO

    def candles_are_initialized(self, time_frame):
        if time_frame in self.symbol_candles and self.symbol_candles[time_frame].is_initialized:
            return True
        elif time_frame is None:
            return True
        return False

    def ticker_is_initialized(self) -> bool:
        return True if self.symbol_ticker is not None else False

    def get_symbol_prices(self, time_frame, limit=None, return_list=False):
        try:
            return self.get_candle_data(time_frame).get_symbol_prices(limit, return_list)
        except AttributeError:
            # if get_candle_data returned None: no candles on this timeframe
            self.logger.error(f"Trying retrieve candle data on {time_frame}: no candle for this time frame.")
            return None
