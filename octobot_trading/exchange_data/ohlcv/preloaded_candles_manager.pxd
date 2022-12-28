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
cimport octobot_trading.exchange_data.ohlcv.candles_manager as candles_manager
cimport numpy as np


cdef class PreloadedCandlesManager(candles_manager.CandlesManager):
    cpdef int get_preloaded_symbol_candles_count(self)
    cpdef np.ndarray get_preloaded_symbol_close_candles(self)
    cpdef np.ndarray get_preloaded_symbol_open_candles(self)
    cpdef np.ndarray get_preloaded_symbol_high_candles(self)
    cpdef np.ndarray get_preloaded_symbol_low_candles(self)
    cpdef np.ndarray get_preloaded_symbol_time_candles(self)
    cpdef np.ndarray get_preloaded_symbol_volume_candles(self)

    # private
    cdef int _get_candle_index(self, list candle)
    cdef np.ndarray _get_candle_values_array(self, list candles, int key)
