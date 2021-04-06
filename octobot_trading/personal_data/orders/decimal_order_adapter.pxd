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

cpdef object decimal_adapt_price(dict symbol_market, object price)
cpdef object decimal_adapt_quantity(dict symbol_market, object quantity)
cpdef list decimal_adapt_order_quantity_because_quantity(object limiting_value, object max_value, object quantity_to_adapt, object price, dict symbol_market)
cpdef list decimal_adapt_order_quantity_because_price(object limiting_value, object max_value, object price, dict symbol_market)
cpdef list decimal_split_orders(object total_order_price, object max_cost, object valid_quantity, object max_quantity, object price, object quantity, dict symbol_market)
cpdef decimal_check_and_adapt_order_details_if_necessary(object quantity, object price, dict symbol_market, object fixed_symbol_data=*)
