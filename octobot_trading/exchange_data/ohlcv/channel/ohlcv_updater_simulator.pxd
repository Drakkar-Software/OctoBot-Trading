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
cimport async_channel.consumer as consumer
cimport octobot_backtesting.importers as importers
cimport octobot_trading.exchange_data.ohlcv.channel.ohlcv_updater as ohlcv_updater


cdef class OHLCVUpdaterSimulator(ohlcv_updater.OHLCVUpdater):
    cdef importers.ExchangeDataImporter exchange_data_importer

    cdef str exchange_name

    cdef double initial_timestamp
    cdef double last_timestamp_pushed
    cdef dict time_frames_to_second

    cdef public consumer.Consumer time_consumer

    cdef object future_candle_time_frame
    cdef int future_candle_sec_length

    cdef dict last_candles_by_pair_by_time_frame
    cdef bint require_last_init_candles_pairs_push
    cdef list traded_pairs
    cdef list traded_time_frame
