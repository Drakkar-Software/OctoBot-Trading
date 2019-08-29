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


cpdef adapt_price(symbol_market, price)
cpdef adapt_quantity(symbol_market, quantity)
cpdef trunc_with_n_decimal_digits(value, digits)
cpdef adapt_order_quantity_because_quantity(limiting_value, max_value, quantity_to_adapt, price, symbol_market)
cpdef adapt_order_quantity_because_price(limiting_value, max_value, price, symbol_market)
cpdef check_factor(min_val, max_val, factor)
cpdef is_valid(element, key)
cpdef get_min_max_amounts(symbol_market, default_value=*)
cpdef check_cost(total_order_price, min_cost)
cpdef check_and_adapt_order_details_if_necessary(quantity, price, symbol_market, fixed_symbol_data=*)
cpdef split_orders(total_order_price, max_cost, valid_quantity, max_quantity, price, quantity, symbol_market)
cpdef add_dusts_to_quantity_if_necessary(quantity, price, symbol_market, current_symbol_holding)


