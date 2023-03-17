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


cimport octobot_trading.personal_data.portfolios.portfolio as portfolio
cimport octobot_trading.personal_data.portfolios.portfolio_manager as portfolio_manager
cimport octobot_trading.personal_data.portfolios.value_converter as value_converter

cdef class PortfolioValueHolder:
    cdef object logger
    cdef object config

    cdef public object portfolio_origin_value
    cdef public object portfolio_current_value
    cdef public value_converter.ValueConverter value_converter

    cdef public dict origin_crypto_currencies_values
    cdef public dict current_crypto_currencies_values

    cdef public portfolio.Portfolio origin_portfolio

    cdef public portfolio_manager.PortfolioManager portfolio_manager

    cpdef bint update_origin_crypto_currencies_values(self, str symbol, object mark_price)
    cpdef dict get_current_crypto_currencies_values(self)
    cpdef dict get_current_holdings_values(self)
    cpdef void reset_portfolio_values(self)
    cpdef object get_origin_portfolio_current_value(self, bint refresh_values=*)
    cpdef object handle_profitability_recalculation(self, bint force_recompute_origin_portfolio)
    cpdef void clear(self)

    cdef object _init_portfolio_values_if_necessary(self, bint force_recompute_origin_portfolio)
    cdef object _init_origin_portfolio_and_currencies_value(self)
    cdef object _update_portfolio_current_value(self, dict portfolio, dict currencies_values=*, bint fill_currencies_values=*)
    cdef void _fill_currencies_values(self, dict currencies_values)
    cdef dict _update_portfolio_and_currencies_current_value(self)
    cdef void _recompute_origin_portfolio_initial_value(self)
    cdef object _evaluate_config_crypto_currencies_and_portfolio_values(self,
                                                                dict portfolio,
                                                                bint ignore_missing_currency_data=*)
    cdef void _evaluate_config_currencies_values(self,
                                                 dict evaluated_pair_values,
                                                 set evaluated_currencies,
                                                 set missing_tickers)
    cdef void _evaluate_portfolio_currencies_values(self,
                                                    dict portfolio,
                                                    dict evaluated_pair_values,
                                                    set valuated_currencies,
                                                    set missing_tickers,
                                                    bint ignore_missing_currency_data)
    cdef object _evaluate_portfolio_value(self, dict portfolio, dict currencies_values=*)
    cdef bint _should_currency_be_considered(self, str currency, dict portfolio, bint ignore_missing_currency_data)
