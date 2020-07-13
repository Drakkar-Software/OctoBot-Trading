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
from octobot_trading.exchanges.websockets.abstract_websocket cimport AbstractWebsocket


cdef class OctoBotWebSocketClient(AbstractWebsocket):
    cdef public str exchange_name

    cdef public list octobot_websockets
    cdef public list octobot_websockets_tasks
    cdef public list trader_pairs
    cdef public list time_frames
    cdef public list channels

    cdef public object octobot_websockets_executors
    cdef public object exchange_class

    cdef public dict open_sockets_keys
    cdef public dict handled_feeds

    cdef public bint is_websocket_running
    cdef public bint is_websocket_authenticated

    # private
    cdef void _create_octobot_feed_feeds(self)

    # public
    cpdef bint is_handling(self, str feed_name)
    cpdef bint is_feed_available(self, object feed)
    cpdef bint is_feed_requiring_init(self, object feed)
