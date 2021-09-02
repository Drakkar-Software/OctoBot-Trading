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
cimport octobot_trading.personal_data.portfolios.portfolio as portfolio_class

cdef class FuturePortfolio(portfolio_class.Portfolio):
    cdef void _update_portfolio_from_future_order(self,
                                              object order,
                                              object order_quantity,
                                              object order_price,
                                              bint subtract_fees=*,
                                              bint inverse_calculation=*,
                                              bint update_available=*,
                                              bint update_total=*)
