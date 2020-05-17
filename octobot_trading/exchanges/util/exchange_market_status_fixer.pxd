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

cpdef bint is_ms_valid(object value, bint zero_valid=*)

cdef void calculate_costs(dict market_limit)
cdef void calculate_prices(dict market_limit)
cdef void calculate_amounts(dict market_limit)
cdef object get_markets_limit(dict market_limit)
cdef void fix_market_status_limits_from_current_data(dict market_limit)
cdef bint check_market_status_limits(market_limit)
cdef bint check_market_status_values(market_limit, bint zero_valid=*)

cdef class ExchangeMarketStatusFixer:
    cdef public object market_status
    cdef public object price_example
    cdef public object market_status_specific

    cdef void __fix_market_status_precision(self)
    cdef void __fix_market_status_limits(self)
    cdef object __calculate_amount(self)
    cdef void __fix_market_status_limits_with_price(self)
    cdef double __get_price_precision(self)
    cdef void __fix_market_status_precision_with_price(self)
    cdef void __fix_market_status_precision_with_specific(self)
    cdef void __fix_market_status_limits_with_specific(self)
