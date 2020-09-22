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

cdef class CCXTExchange(AbstractExchange):
    cdef object all_currencies_price_ticker
    cdef public object client

    # private
    cdef void _create_client(self)
    cdef void _log_error(self, object error, object order_type, str symbol, double quantity, double price, double stop_price)

    # @staticmethod TODO
    # cdef bint _ensure_order_details_completeness(object order, list order_required_fields=*)

    cpdef dict get_ccxt_client_login_options(self)
    cpdef void set_sandbox_mode(self, bint is_sandboxed)
