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
cimport octobot_trading.exchanges.abstract_websocket_exchange as abstract_websocket

cdef class AbstractWebsocketConnector(abstract_websocket.AbstractWebsocketExchange):
    cdef int timeout
    cdef int timeout_interval
    cdef int last_ping_time

    cdef bint is_connected
    cdef bint should_stop
    cdef bint is_authenticated
    cdef bint use_testnet

    cdef public dict endpoint_args

    # objects
    cdef public object websocket
    cdef object _watch_task
    cdef object last_msg

    cpdef void on_open(self)
    cpdef void on_auth(self, bint status)
    cpdef void on_close(self)
    cpdef void on_error(self, str error)
    cpdef void start(self)
