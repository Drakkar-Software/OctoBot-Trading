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
    cpdef object update_portfolio_from_funding(self, object position, object funding_rate)  # needs object to forward exceptions
    cpdef object update_portfolio_from_pnl(self, object position)  # needs object to forward exceptions
    cpdef object update_portfolio_data_from_position_size_update(self, object position,
                                                                 object realized_pnl_update,
                                                                 object size_update,
                                                                 object margin_update,
                                                                 bint has_increased_position_size)  # needs object to forward exceptions

    # needs object to forward exceptions
    cdef object _update_future_portfolio_data(self, str currency,
                                              object wallet_value=*,
                                              object position_margin_value=*,
                                              object order_margin_value=*,
                                              object unrealized_pnl_value=*,
                                              object initial_margin_value=*,
                                              bint replace_value=*)
