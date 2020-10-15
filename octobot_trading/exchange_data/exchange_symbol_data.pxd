# cython: language_level=3
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
#  Lesser General License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
cimport octobot_trading.exchange_data as exchange_data

cdef class ExchangeSymbolData:
    cdef public str symbol

    cdef object logger
    cdef public object exchange_manager

    cdef public dict symbol_candles
    cdef public dict symbol_klines

    cdef public exchange_data.PriceEventsManager price_events_manager
    cdef public exchange_data.OrderBookManager order_book_manager
    cdef public exchange_data.PricesManager prices_manager
    cdef public exchange_data.RecentTradesManager recent_trades_manager
    cdef public exchange_data.TickerManager ticker_manager
    cdef public exchange_data.FundingManager funding_manager

    cpdef list handle_recent_trade_update(self, list recent_trades, bint replace_all=*)
    cpdef void handle_order_book_update(self, list asks, list bids)
    cpdef void handle_order_book_ticker_update(self, double ask_quantity, double ask_price,
                                               double bid_quantity, double bid_price)
    cpdef bint handle_mark_price_update(self, double mark_price, str mark_price_source)
    cpdef void handle_ticker_update(self, dict ticker)
    cpdef void handle_mini_ticker_update(self, dict mini_ticker)
