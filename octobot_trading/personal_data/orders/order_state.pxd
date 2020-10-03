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
from octobot_trading.util.initializable cimport Initializable

cdef class OrderState(Initializable):
    cdef public object order  # instance of Order
    cdef public object state  # item of OrderStates
    cdef public object lock  # item of asyncio.Lock

    cdef public bint is_from_exchange_data

    cpdef bint is_refreshing(self)
    cpdef bint is_open(self)
    cpdef bint is_pending(self)
    cpdef bint is_filled(self)
    cpdef bint is_closed(self)
    cpdef bint is_canceled(self)
    cpdef void clear(self)
    cpdef void log_order_event_message(self, str state_message)
