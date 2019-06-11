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
from octobot_trading.data_manager.candles_manager cimport CandlesManager
from octobot_trading.data_manager.order_book_manager cimport OrderBookManager
from octobot_trading.data_manager.recent_trades_manager cimport RecentTradesManager
from octobot_trading.data_manager.ticker_manager cimport TickerManager

cdef class ExchangeSymbolData:
    cdef public str symbol

    cdef object logger

    cdef dict symbol_candles

    cdef public bint are_recent_trades_initialized
    cdef public bint is_order_book_initialized
    cdef public bint is_price_ticker_initialized

    cdef public CandlesManager candles_manager
    cdef public OrderBookManager order_book_manager
    cdef public RecentTradesManager recent_trades_manager
    cdef public TickerManager ticker_manager

    cpdef void handle_recent_trades(self, list recent_trades)
    cpdef void handle_recent_trade_update(self, dict recent_trade)
    cpdef void handle_order_book_update(self, list asks, list bids)
    cpdef void handle_order_book_delta_update(self, list asks, list bids)
    cpdef void handle_ticker_update(self, dict ticker)
