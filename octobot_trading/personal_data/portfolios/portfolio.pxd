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

cimport octobot_trading.personal_data.orders.order as order_class

cdef class Portfolio:
    cdef object logger # Logger
    cdef public object lock # asyncio.Lock

    cdef public dict portfolio

    cdef str _exchange_name

    cdef bint _is_simulated

    # public methods
    cpdef void reset(self)
    # return object to ensure PortfolioNegativeValueError forwarding
    # cpdef object update_portfolio_from_balance(self, dict balance, bint force_replace=*) can't be cythonized for now
    cpdef object get_currency_portfolio(self, str currency)
    cpdef object update_portfolio_from_filled_order(self, order_class.Order order)
    cpdef object update_portfolio_available(self, order_class.Order order, bint is_new_order= *)
    # cpdef dict get_portfolio_from_amount_dict(self, dict amount_dict) can't be cythonized for now
    cpdef void reset_portfolio_available(self, str reset_currency= *, object reset_quantity= *)
    cpdef void log_portfolio_update_from_order(self, order_class.Order order)

    # abstract methods
    # return object to ensure PortfolioNegativeValueError forwarding
    cpdef object update_portfolio_data_from_order(self, order_class.Order order)
    cpdef object update_portfolio_available_from_order(self, order_class.Order order, bint is_new_order=*)
    cpdef object create_currency_asset(self, str currency, object available=*, object total=*)

    # private methods
    # return object to ensure PortfolioNegativeValueError forwarding
    cdef object _update_portfolio_data(self, str currency, object total_value=*, object available_value=*,
                                       bint replace_value=*)
    cdef object _parse_raw_currency_asset(self, str currency, dict raw_currency_balance)
    cdef bint _update_raw_currency_asset(self, str currency, dict raw_currency_balance)
    cdef void _reset_all_portfolio_available(self)
    cdef object _reset_currency_portfolio_available(self, str currency_to_reset, object reset_quantity)

cdef bint _should_update_available(order_class.Order order)
cdef tuple _parse_raw_currency_balance(dict raw_currency_balance)
