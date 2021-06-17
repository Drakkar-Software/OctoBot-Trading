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
cimport octobot_trading.util as util

cdef class State(util.Initializable):
    cdef public object state  # item of OrderStates
    cdef public object lock  # item of asyncio.Lock

    cdef public bint is_from_exchange_data

    cpdef bint is_refreshing(self)
    cpdef bint is_open(self)
    cpdef bint is_pending(self)
    cpdef bint is_closed(self)
    cpdef void clear(self)
    cpdef object get_logger(self)
    cpdef void log_event_message(self, object state_message, object error=*)
