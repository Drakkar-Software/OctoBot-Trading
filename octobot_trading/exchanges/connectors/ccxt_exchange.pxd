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
cimport octobot_trading.exchanges.abstract_exchange as abstract_exchange

cdef class CCXTExchange(abstract_exchange.AbstractExchange):
    cdef object all_currencies_price_ticker

    cdef public object client
    cdef public object exchange_type

    cdef public bint is_authenticated

    # private
    cdef void _create_client(self)

    # @staticmethod waiting for a future version of cython
    # cdef bint _ensure_order_details_completeness(object order, list order_required_fields=*)

    cpdef dict get_ccxt_client_login_options(self)
    cpdef void set_sandbox_mode(self, bint is_sandboxed)
    cpdef void log_error(self, object error, object order_type, str symbol, double quantity, double price, double stop_price)
