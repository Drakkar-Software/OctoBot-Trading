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

cdef class WebsocketExchange:
    cdef public str exchange_id
    cdef str api_key
    cdef str api_secret
    cdef str api_password

    cdef int timeout
    cdef int timeout_interval
    cdef int last_ping_time

    cdef bint is_connected
    cdef bint should_stop
    cdef bint use_testnet
    cdef bint is_authenticated

    cdef public list currencies
    cdef public list pairs
    cdef public list time_frames
    cdef public list channels

    # objects
    cdef public object exchange_manager
    cdef public object exchange
    cdef public object logger
    cdef public object websocket
    cdef public object websocket_task
    cdef public object ccxt_client
    cdef public object async_ccxt_client
    cdef object _watch_task
    cdef object last_msg
    cdef object loop

    cdef void _initialize(self, list pairs, list channels)
    cdef void on_open(self)
    cdef void on_auth(self, bint status)
    cdef void on_close(self)
    cdef void on_error(self, str error)
    cdef list get_pairs(self)
    cdef double fix_timestamp(self, double ts)
    cdef double timestamp_normalize(self, double ts)
    cdef str feed_to_exchange(self, feed)

    cpdef start(self)
    cpdef stop(self)
    cpdef close(self)

    @staticmethod
    cdef object _convert_seconds_to_time_frame(int time_frame_seconds)

    @staticmethod
    cdef int _convert_time_frame_minutes_to_seconds(object time_frame)
