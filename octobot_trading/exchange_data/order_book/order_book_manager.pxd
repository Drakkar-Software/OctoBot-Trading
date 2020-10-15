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
cimport octobot_trading.util as util


cdef class OrderBookManager(util.Initializable):
    cdef object logger

    cdef public bint order_book_initialized

    cdef public double ask_quantity
    cdef public double ask_price
    cdef public double bid_quantity
    cdef public double bid_price

    cdef public object asks # SortedDict
    cdef public object bids # SortedDict

    cdef public double timestamp

    cpdef void reset_order_book(self)
    cpdef void order_book_ticker_update(self, double ask_quantity, double ask_price,
                                        double bid_quantity, double bid_price)
    cpdef void handle_new_book(self, dict orders)
    cpdef void handle_new_books(self, list asks, list bids, object timestamp=*)
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
cdef list _convert_price_size_list_to_order(list price_size_list, str side)
cdef dict _convert_price_size_to_order(list price_size, str side)
