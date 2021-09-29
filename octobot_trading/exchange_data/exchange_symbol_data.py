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

import octobot_commons.logging as logging

import octobot_trading.exchange_data.ohlcv.candles_manager as candles_manager
import octobot_trading.exchange_data.ticker.ticker_manager as ticker_manager
import octobot_trading.exchange_data.order_book.order_book_manager as order_book_manager
import octobot_trading.exchange_data.kline.kline_manager as kline_manager
import octobot_trading.exchange_data.prices.prices_manager as prices_manager
import octobot_trading.exchange_data.prices.price_events_manager as price_events_manager
import octobot_trading.exchange_data.recent_trades.recent_trades_manager as recent_trades_manager
import octobot_trading.exchange_data.funding.funding_manager as funding_manager


class ExchangeSymbolData:
    MAX_ORDER_BOOK_ORDER_COUNT = 100
    MAX_RECENT_TRADES_COUNT = 100

    def __init__(self, exchange_manager, symbol):
        self.symbol = symbol
        self.exchange_manager = exchange_manager

        self.price_events_manager = price_events_manager.PriceEventsManager()
        self.order_book_manager = order_book_manager.OrderBookManager()
        self.prices_manager = prices_manager.PricesManager(self.exchange_manager)
        self.recent_trades_manager = recent_trades_manager.RecentTradesManager()
        self.ticker_manager = ticker_manager.TickerManager()
        self.funding_manager = funding_manager.FundingManager() \
            if self.exchange_manager.is_margin or self.exchange_manager.is_future else None

        self.symbol_candles = {}
        self.symbol_klines = {}

        self.logger = logging.get_logger(f"{self.__class__.__name__} - {self.symbol}")

    # candle functions
    async def handle_candles_update(self, time_frame, new_symbol_candles_data, replace_all=False, partial=False):
        try:
            symbol_candles = self.symbol_candles[time_frame]
        except KeyError:
            symbol_candles = candles_manager.CandlesManager()
            await symbol_candles.initialize()

            if replace_all:
                symbol_candles.replace_all_candles(new_symbol_candles_data)

            self.symbol_candles[time_frame] = symbol_candles
            return

        if partial:
            symbol_candles.add_old_and_new_candles(new_symbol_candles_data)
        elif replace_all:
            symbol_candles.replace_all_candles(new_symbol_candles_data)
        else:
            symbol_candles.add_new_candle(new_symbol_candles_data)

    def handle_recent_trade_update(self, recent_trades, replace_all=False):
        if replace_all:
            recent_trades_added = self.recent_trades_manager.set_all_recent_trades(recent_trades)
        else:
            recent_trades_added = self.recent_trades_manager.add_new_trades(recent_trades)
        self.price_events_manager.handle_recent_trades(recent_trades_added)
        return recent_trades_added

    def handle_liquidations(self, liquidations):
        self.recent_trades_manager.add_new_liquidations(liquidations)

    def handle_mark_price_update(self, mark_price, mark_price_source) -> bool:
        updated = self.prices_manager.set_mark_price(mark_price, mark_price_source)
        if updated:
            self.price_events_manager.handle_price(mark_price,
                                                   self.exchange_manager.exchange.get_exchange_current_time())
        return updated

    def handle_order_book_update(self, asks, bids):
        self.order_book_manager.handle_new_books(asks, bids)

    def handle_order_book_ticker_update(self, ask_quantity, ask_price, bid_quantity, bid_price):
        self.order_book_manager.order_book_ticker_update(ask_quantity, ask_price, bid_quantity, bid_price)

    def handle_ticker_update(self, ticker):
        self.ticker_manager.ticker_update(ticker)

    def handle_mini_ticker_update(self, mini_ticker):
        self.ticker_manager.mini_ticker_update(mini_ticker)

    async def handle_kline_update(self, time_frame, kline):
        try:
            symbol_klines = self.symbol_klines[time_frame]
        except KeyError:
            symbol_klines = kline_manager.KlineManager()
            try:
                await symbol_klines.initialize()
                symbol_klines.kline_update(kline)
                self.symbol_klines[time_frame] = symbol_klines
            except KeyError:
                self.logger.warning("Can't initialize kline manager : missing required candles data.")
                return

        symbol_klines.kline_update(kline)

    async def handle_funding_update(self, funding_rate, predicted_funding_rate, next_funding_time, timestamp):
        if self.funding_manager:
            self.funding_manager.funding_update(funding_rate, predicted_funding_rate, next_funding_time, timestamp)
