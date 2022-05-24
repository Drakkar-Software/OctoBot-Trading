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
cimport octobot_trading.personal_data.portfolios.portfolio_manager as portfolio_manager
cimport octobot_trading.personal_data.portfolios.portfolio_value_holder as portfolio_value_holder

cdef class PortfolioProfitability:
    cdef object logger

    cdef portfolio_manager.PortfolioManager portfolio_manager
    cdef portfolio_value_holder.PortfolioValueHolder value_manager

    cdef public object profitability
    cdef public object profitability_percent
    cdef public object profitability_diff
    cdef public object market_profitability_percent
    cdef public object initial_portfolio_current_profitability

    cdef set traded_currencies_without_market_specific
    cdef public set valuated_currencies

    cpdef object update_profitability(self, bint force_recompute_origin_portfolio=*)

    cdef object _calculate_average_market_profitability(self)
    cdef void _reset_before_profitability_calculation(self)
    cdef object _update_profitability_calculation(self)
    cdef object _update_portfolio_delta(self)
    cdef dict _only_symbol_currency_filter(self, dict currency_dict)
    # cdef void _init_traded_currencies_without_market_specific(self) can't be cythonized for now
