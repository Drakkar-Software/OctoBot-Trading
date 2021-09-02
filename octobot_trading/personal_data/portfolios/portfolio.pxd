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


""" Order class will represent an open order in the specified exchange
In simulation it will also define rules to be filled / canceled
It is also use to store creation & fill values of the order """
cimport octobot_trading.personal_data.orders.order as order_class
cimport octobot_trading.util as util

cdef class Portfolio(util.Initializable):
    cdef object logger # Logger
    cdef public object lock # asyncio.Lock

    cdef public dict portfolio

    cdef str _exchange_name

    cdef bint _is_simulated

    # public methods
    cpdef object get_currency_portfolio(self, str currency, str portfolio_type=*)
    cpdef object get_currency_from_given_portfolio(self, str currency, str portfolio_type=*)
    cpdef void reset_portfolio_available(self, str reset_currency=*, object reset_quantity=*)
    cpdef void reset(self)
    # return object to ensure PortfolioNegativeValueError forwarding
    cpdef object update_portfolio_from_balance(self, dict balance, bint force_replace=*)
    cpdef object update_portfolio_available(self, order_class.Order order, bint is_new_order=*)
    cpdef object update_portfolio_from_filled_order(self, order_class.Order order)
    # cpdef dict get_portfolio_from_amount_dict(self, dict amount_dict) can't be cythonized for now

    # abstract methods
    cpdef void log_portfolio_update_from_order(self, order_class.Order order, str currency, str market)
    # return object to ensure PortfolioNegativeValueError forwarding
    cpdef object update_portfolio_data_from_order(self, order_class.Order order, str currency, str market)
    cpdef object update_portfolio_available_from_order(self, order_class.Order order, bint increase_quantity=*)

    # private methods
    cdef void _reset_currency_portfolio(self, str currency)
    cdef dict _parse_currency_balance(self, dict currency_balance)
    cdef dict _create_currency_portfolio(self, object available, object total)
    cdef void _set_currency_portfolio(self, str currency, object available, object total)
    cdef void _reset_all_portfolio_available(self)
    # return object to ensure PortfolioNegativeValueError forwarding
    cdef object _update_portfolio_data(self, str currency, object value, bint total=*, bint available=*)
    cdef object _update_currency_portfolio(self, str currency, object available=*, object total=*)
    cdef object _reset_currency_portfolio_available(self, str currency_to_reset, object reset_quantity)

cdef bint _should_update_available(order_class.Order order)

cpdef object ensure_portfolio_update_validness(str currency, object origin_quantity, object update_quantity)
