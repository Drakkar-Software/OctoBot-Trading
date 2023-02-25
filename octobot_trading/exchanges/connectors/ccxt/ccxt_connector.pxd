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

cdef class CCXTConnector(abstract_exchange.AbstractExchange):
    cdef object all_currencies_price_ticker

    cdef public object client
    cdef public object exchange_type
    cdef public object adapter
    cdef public bint is_authenticated
    cdef public str rest_name

    cdef object additional_config
    cdef dict options
    cdef dict headers


    # private
    cdef object _create_client(self)

    # @staticmethod waiting for a future version of cython
    # cdef bint _ensure_order_details_completeness(object order, list order_required_fields=*)

    cpdef object get_adapter_class(self, object adapter_class)
    cpdef void add_headers(self, dict headers_dict)
    cpdef void add_options(self, dict options_dict)
    cpdef set get_client_symbols(self)
    cpdef set get_client_time_frames(self)
    cpdef str get_ccxt_order_type(self, object order_type)
    cpdef object unauthenticated_exchange_fallback(self, object err)

    cdef bint _should_authenticate(self)
