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
cimport octobot_trading.personal_data.portfolios.portfolio as portfolio_class
cimport octobot_trading.personal_data.orders.order as order_class

cdef class SubPortfolio(portfolio_class.Portfolio):
    cdef public portfolio_class.Portfolio parent_portfolio

    cdef public object percent

    cdef public bint is_relative

    cpdef void update_from_parent(self)
    cpdef void set_percent(self, object percent)
    cpdef object update_portfolio_available(self, order_class.Order order, bint is_new_order=*)
    cpdef void reset_portfolio_available(self, str reset_currency=*, object reset_quantity=*)