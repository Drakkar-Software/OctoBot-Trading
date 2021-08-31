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
cimport octobot_trading.exchanges.exchange_manager as exchange_manager

cdef class AbstractWebsocketExchange:
    cdef public dict config
    cdef public dict books

    cdef public exchange_manager.ExchangeManager exchange_manager

    cdef public str name
    cdef public str exchange_id

    cdef public list currencies
    cdef public list pairs
    cdef public list time_frames
    cdef public list channels

    cdef public object exchange
    cdef public object client
    cdef public object logger
    cdef public object bot_mainloop

    cpdef object get_exchange_credentials(self)
    cpdef object get_book_instance(self, str symbol)

    cpdef void add_pairs(self, list pairs, bint watching_only=*)
    cpdef void add_time_frames(self, list time_frames)
    cpdef void initialize(self, list currencies=*, list pairs=*, list time_frames=*, list channels=*)

    cpdef bint _should_authenticate(self)

    cpdef int get_max_handled_pair_with_time_frame(self)

    cpdef str feed_to_exchange(self, object feed)
    cpdef str get_pair_from_exchange(self, str pair)
    cpdef str get_exchange_pair(self, str pair)
    cpdef void clear(self)
