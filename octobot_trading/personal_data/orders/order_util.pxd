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

cpdef bint is_valid(object element, object key)
cpdef object get_min_max_amounts(dict symbol_market, object default_value=*)
cpdef bint check_cost(double total_order_price, object min_cost)
cpdef object total_fees_from_order_dict(dict order_dict, str currency)
cpdef object get_fees_for_currency(object fee, str currency)
cpdef dict parse_raw_fees(object raw_fees)
cpdef object parse_order_status(dict raw_order)
cpdef bint parse_is_cancelled(dict raw_order)
