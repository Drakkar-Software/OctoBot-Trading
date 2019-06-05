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
from octobot_trading.exchanges.abstract_exchange cimport AbstractExchange
from octobot_trading.exchanges.backtesting.backtesting cimport Backtesting

cdef class ExchangeSimulator(AbstractExchange):
    cdef public bint initializing

    cdef public list symbols
    cdef public list config_time_frames

    cdef public dict data
    cdef public dict time_frame_get_times
    cdef public dict time_frames_offset
    cdef public dict min_time_frame_to_consider

    cdef public int DEFAULT_LIMIT
    cdef public int MIN_LIMIT
    cdef public int RECENT_TRADES_TO_CREATE
    cdef public int recent_trades_multiplier_factor

    cdef public object MIN_ENABLED_TIME_FRAME
    cdef public object DEFAULT_TIME_FRAME_RECENT_TRADE_CREATOR
    cdef public object DEFAULT_TIME_FRAME_TICKERS_CREATOR

    cdef public Backtesting backtesting

    # private
    cdef dict _get_available_timeframes(self)
    cdef void _set_symbol_list(self, str config_backtesting_data_files_path)
    cdef dict _fix_timestamps(self, dict data)
    cdef void _prepare(self)
    cdef float _get_current_timestamp(self, object time_frame, str symbol, int backwards=*)
    cdef dict _create_ticker(self, str symbol, int index)
    cdef list _fetch_recent_trades(self, str symbol, object timeframe, int index)
    cdef list _generate_trades(self, object time_frame, float timestamp)
    cdef int _get_candle_index(self, object time_frame, str symbol)
    cdef list _extract_data_with_limit(self, str symbol, object time_frame)
    cdef void _ensure_available_data(self, str symbol)
    cdef dict get_candles_exact(self, str symbol, object time_frame, int min_index, int max_index, bint return_list=*)
    cdef dict get_full_candles_data(self, str symbol, object time_frame)
    cdef list _get_used_time_frames(self, str symbol)
    cdef object _find_min_time_frame_to_consider(self, list time_frames, str symbol)

    @staticmethod
    cdef list _extract_from_indexes(list array, int max_index, str symbol, int factor=*)

    cpdef dict get_ohlcv(self, str symbol)
    cpdef dict get_trades(self, str symbol)
    cpdef handles_trades_history(self, str symbol)
    cpdef bint symbol_exists(self, str symbol)
    cpdef bint time_frame_exists(self, object time_frame)
    cpdef bint has_data_for_time_frame(self, str symbol, object time_frame)
    cpdef str get_name(self)
    cpdef bint should_update_data(self, object time_frame, str symbol)
    cpdef void init_candles_offset(self, list time_frames, str symbol)
    cpdef object get_min_time_frame(self, str symbol)
    cpdef int get_progress(self)
    cpdef dict get_market_status(self, str symbol, float price_example=*, bint with_fixer=*)
    cpdef get_uniform_timestamp(self, float timestamp)
    cpdef dict get_fees(self, str symbol=*)
    cpdef dict get_trade_fee(self, str symbol, object order_type, float quantity, float price, str taker_or_maker=*)
