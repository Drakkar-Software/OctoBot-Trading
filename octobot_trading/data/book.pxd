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
    cdef object logger
    cdef public object asks # SortedDict
    cdef public object bids # SortedDict

    cdef public double timestamp

    cpdef void reset(self)
    cpdef void handle_new_book(self, dict orders)
    cpdef void handle_book_adds(self, list orders)
    cpdef void handle_book_deletes(self, list orders)
    cpdef void handle_book_updates(self, list orders)
    cpdef tuple get_ask(self)
    cpdef tuple get_bid(self)
    cpdef object get_asks(self, double price)
    cpdef object get_bids(self, double price)

    cdef object _handle_book_delete(self, dict order) # using object to prevent ignoring KeyError
    cdef object _handle_book_update(self, dict order) # using object to prevent ignoring KeyError
    cdef object _handle_book_add(self, dict order) # using object to prevent ignoring KeyError
    cdef void _set_asks(self, double price, list asks)
    cdef void _set_bids(self, double price, list bids)
    cdef void _remove_asks(self, double price)
    cdef void _remove_bids(self, double price)

cdef int _order_id_index(str order_id, list order_list)
