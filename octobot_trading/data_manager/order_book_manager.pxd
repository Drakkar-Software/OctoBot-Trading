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

from octobot_trading.util.initializable cimport Initializable


cdef class OrderBookManager(Initializable):
    cdef object logger

    cdef public bint order_book_initialized

    cdef public double ask_quantity
    cdef public double ask_price
    cdef public double bid_quantity
    cdef public double bid_price

    cdef public list bids
    cdef public list asks

    cpdef void reset_order_book(self)
    cpdef void order_book_update(self, list asks, list bids)
    cpdef void order_book_ticker_update(self, double ask_quantity, double ask_price,
                                        double bid_quantity, double bid_price)
