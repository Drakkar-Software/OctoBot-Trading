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
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
cimport octobot_trading.exchange_data.ohlcv.channel.ohlcv as ohlcv_channel


cdef class OHLCVUpdater(ohlcv_channel.OHLCVProducer):
    cdef list tasks

    cdef bint is_initialized
    cdef dict initialized_candles_by_tf_by_symbol

    cdef list _get_traded_pairs(self)
    cdef list _get_time_frames(self)
    cdef int _get_historical_candles_count(self)
    cdef double _ensure_correct_sleep_time(self, double sleep_time_candidate, double time_frame_sleep)
    cdef void _set_initialized(self, str pair, object time_frame, bint initialized)
