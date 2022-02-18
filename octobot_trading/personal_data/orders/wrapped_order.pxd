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


cdef class WrappedOrder:
    cdef public object order  # instance of Order
    cdef public object triggered_by  # instance of Order
    cdef public object portfolio
    cdef public bint to_be_fetched_only
    cdef public dict params
    cdef public dict kwargs

    cdef public bint created
    cdef public object created_order  # instance of Order

    cpdef bint should_be_created(self)
