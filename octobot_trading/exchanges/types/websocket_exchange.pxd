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


cdef class WebSocketExchange(abstract_websocket.AbstractWebsocketExchange):
    cdef public str exchange_name

    cdef public list websocket_connectors_tasks
    cdef public list websocket_connectors

    cdef public object websocket_connectors_executors
    cdef public object websocket_connector

    cdef public dict open_sockets_keys
    cdef public dict handled_feeds

    cdef public bint is_websocket_running
    cdef public bint is_websocket_authenticated

    cdef public object restart_task

    # public
    cpdef bint is_handling(self, str feed_name)
    cpdef bint is_feed_available(self, object feed)
    cpdef bint is_feed_requiring_init(self, object feed)
    cpdef void create_feeds(self)
