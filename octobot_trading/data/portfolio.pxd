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

cdef class Portfolio:
    cdef object config
    cdef object trader
    cdef object exchange_manager
    cdef object logger
    cdef public object lock

    cdef public bint is_simulated
    cdef public bint is_enabled

    cdef public dict portfolio

    cpdef void set_starting_simulated_portfolio(self)
    cpdef float get_currency_portfolio(self, str currency, str portfolio_type=*)
    cpdef void update_portfolio_available(self, Order order, bint is_new_order=*)
    cpdef void reset_portfolio_available(self, str reset_currency=*, float reset_quantity=*)

    cdef void _update_portfolio_data(self, str currency, float value, bint total=*, bint available=*)
    cdef void _update_portfolio_available(self, Order order, float factor=*):

    @staticmethod
    cpdef dict get_portfolio_from_amount_dict(dict amount_dict)
    @staticmethod
    cpdef float get_currency_from_given_portfolio(Portfolio portfolio, str currency, str portfolio_type=*)
    @staticmethod
    cpdef bint _check_available_should_update(Order order)
