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

    cdef public dict endpoint_args

    cdef public list currencies
    cdef public list pairs
    cdef public list time_frames
    cdef public list channels

    cdef public dict books

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
    cdef str feed_to_exchange(self, feed)
    cdef bint _should_authenticate(self)

    cpdef start(self)
    cpdef stop(self)
    cpdef close(self)
    cpdef OrderBookManager get_book_instance(self, str symbol)
