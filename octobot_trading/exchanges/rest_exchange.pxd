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

    # balance additional info
    cdef list info_list
    cdef float free
    cdef float used
    cdef float total

    cdef object all_currencies_price_ticker

    # private
    cdef void _create_client(self)
    cdef void _log_error(self, str error, object order_type, str symbol, float quantity, float price, float stop_price)

    # @staticmethod TODO
    # cdef bint _ensure_order_details_completeness(object order, list order_required_fields=*)

    @staticmethod
    cdef str _get_side(object order_type)

    # public
    cpdef get_market_status(self, str symbol, object price_example=*, bint with_fixer=*)
    cpdef get_trade_fee(self, str symbol, object order_type, float quantity, float price, str taker_or_maker=*)
    cpdef dict get_fees(self, str symbol)
    cpdef float get_uniform_timestamp(self, float timestamp)
