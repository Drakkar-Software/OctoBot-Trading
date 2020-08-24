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
from octobot_trading.data.order cimport Order
from octobot_trading.util.initializable cimport Initializable

cdef class Portfolio(Initializable):
    cdef object logger # Logger
    cdef public object lock # asyncio.Lock

    cdef public dict portfolio

    cdef str _exchange_name

    cdef bint _is_simulated

    cpdef double get_currency_portfolio(self, str currency, str portfolio_type=*)
    cpdef double get_currency_from_given_portfolio(self, str currency, str portfolio_type=*)
    cpdef bint update_portfolio_from_balance(self, dict balance)
    cpdef void update_portfolio_available(self, Order order, bint is_new_order=*)
    cpdef void update_portfolio_from_filled_order(self, Order order)
    cpdef void reset_portfolio_available(self, str reset_currency=*, object reset_quantity=*)
    # cpdef dict get_portfolio_from_amount_dict(self, dict amount_dict) can't be cythonized for now
    cpdef void reset(self)

    cdef void _update_portfolio_data(self, str currency, double value, bint total=*, bint available=*)
    cdef void _update_portfolio_data_from_order(self, Order order, str currency, str market)
    cdef void _update_portfolio_available(self, Order order, int factor=*)
    cdef void _reset_currency_portfolio(self, str currency)
    cdef dict _parse_currency_balance(self, dict currency_balance)
    cdef dict _create_currency_portfolio(self, double available, double total)
    cdef void _set_currency_portfolio(self, str currency, double available, double total)
    cdef void _update_currency_portfolio(self, str currency, double available=*, double total=*)
    cdef void _log_portfolio_update(self, Order order, str currency, str market)

cdef bint _check_available_should_update(Order order)
