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
from octobot_trading.exchanges.abstract_exchange cimport AbstractExchange

cdef class RestExchange(AbstractExchange):
    cdef public bint is_authenticated
    cdef public bint is_sandboxed

    # balance additional info
    cdef list info_list
    cdef double free
    cdef double used
    cdef double total

    cdef object all_currencies_price_ticker

    # private
    cdef void __create_client(self)
    cdef void __log_error(self, str error, object order_type, str symbol, double quantity, double price, double stop_price)

    # @staticmethod TODO
    # cdef bint _ensure_order_details_completeness(object order, list order_required_fields=*)

    @staticmethod
    cdef str __get_side(object order_type)

    # public
    cpdef get_market_status(self, str symbol, object price_example=*, bint with_fixer=*)
    cpdef dict get_trade_fee(self, str symbol, object order_type, double quantity, double price, str taker_or_maker)
    cpdef dict get_fees(self, str symbol)
    cpdef double get_uniform_timestamp(self, double timestamp)
    cpdef str get_pair_from_exchange(self, str pair)
    cpdef tuple get_split_pair_from_exchange(self, str pair)
    cpdef void set_sandbox_mode(self, bint is_sandboxed)
    cpdef double get_candle_since_timestamp(self, object time_frame, int count)
