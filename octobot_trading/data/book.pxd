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

cdef class Book:
    cdef public timestamp

    cdef public object orders

    cpdef void reset(self)
    cpdef void handle_book_update(self, list orders, str id_key=*)
    cpdef void handle_book_delta_delete(self, list orders, str id_key=*)
    cpdef void handle_book_delta_update(self, list orders, str id_key=*)
    cpdef void handle_book_delta_insert(self, list orders, str id_key=*)
    cpdef list get_asks(self, str side=*)
    cpdef list get_bids(self, str side=*)