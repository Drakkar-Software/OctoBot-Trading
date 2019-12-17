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
from octobot_trading.data_manager.order_book_manager cimport OrderBookManager
from octobot_trading.data_manager.prices_manager cimport PricesManager
from octobot_trading.data_manager.recent_trades_manager cimport RecentTradesManager
from octobot_trading.data_manager.ticker_manager cimport TickerManager

cdef class ExchangeSymbolData:
    cdef public str symbol

    cdef object logger
    cdef public object exchange_manager

    cdef public dict symbol_candles
    cdef public dict symbol_klines

    cdef public OrderBookManager order_book_manager
    cdef public PricesManager prices_manager
    cdef public RecentTradesManager recent_trades_manager
    cdef public TickerManager ticker_manager

    cpdef list handle_recent_trade_update(self, object recent_trades, bint replace_all=*, bint partial=*) # recent trades can be list or dict
    cpdef void handle_order_book_update(self, list asks, list bids, bint is_delta=*)
    cpdef void handle_mark_price_update(self, float mark_price)
    cpdef void handle_ticker_update(self, dict ticker)
