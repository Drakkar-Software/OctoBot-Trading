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
from octobot_backtesting.importers.exchanges.exchange_importer cimport ExchangeDataImporter
from octobot_trading.exchanges.abstract_exchange cimport AbstractExchange

cdef class ExchangeSimulator(AbstractExchange):
    cdef public bint initializing

    cdef public list symbols
    cdef public list config_time_frames
    cdef public list backtesting_data_files

    cdef public dict data
    cdef public dict time_frame_get_times
    cdef public dict time_frames_offset
    cdef public dict min_time_frame_to_consider

    cdef public int DEFAULT_LIMIT
    cdef public int MIN_LIMIT
    cdef public int RECENT_TRADES_TO_CREATE
    cdef public int recent_trades_multiplier_factor

    cdef public ExchangeDataImporter exchange_importer

    cdef public object MIN_ENABLED_TIME_FRAME
    cdef public object DEFAULT_TIME_FRAME_RECENT_TRADE_CREATOR
    cdef public object DEFAULT_TIME_FRAME_TICKERS_CREATOR

    # cdef public Backtesting backtesting

    cpdef bint symbol_exists(self, str symbol)
    cpdef bint time_frame_exists(self, object time_frame)
    cpdef str get_name(self)
    cpdef int get_progress(self)
    cpdef dict get_market_status(self, str symbol, float price_example=*, bint with_fixer=*)
    cpdef get_uniform_timestamp(self, float timestamp)
    cpdef dict get_fees(self, str symbol=*)
    cpdef dict get_trade_fee(self, str symbol, object order_type, float quantity, float price, str taker_or_maker=*)
