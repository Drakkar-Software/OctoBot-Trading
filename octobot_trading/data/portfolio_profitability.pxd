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
from octobot_trading.data.portfolio cimport Portfolio
from octobot_trading.data_manager.portfolio_manager cimport PortfolioManager
from octobot_trading.exchanges.exchange_manager cimport ExchangeManager
from octobot_trading.traders.trader cimport Trader

cdef class PortfolioProfitabilty:
    cdef object logger
    cdef object config

    cdef PortfolioManager portfolio_manager
    cdef ExchangeManager exchange_manager
    cdef Trader trader

    cdef public double profitability
    cdef public double profitability_percent
    cdef public double profitability_diff
    cdef public double market_profitability_percent
    cdef public double portfolio_origin_value
    cdef public double portfolio_current_value
    cdef public double initial_portfolio_current_profitability
    cdef public set initializing_symbol_prices

    cdef public str reference_market

    cdef public dict currencies_last_prices
    cdef public dict origin_crypto_currencies_values
    cdef public dict current_crypto_currencies_values

    cdef public Portfolio origin_portfolio

    cdef set traded_currencies_without_market_specific
    cdef set traded_currencies
    cdef set missing_currency_data_in_exchange

    cdef dict _only_symbol_currency_filter(self, dict currency_dict)
    cdef void _init_traded_currencies_without_market_specific(self)
    cdef void _inform_no_matching_symbol(self, str currency)
    cdef bint _should_currency_be_considered(self, str currency, dict portfolio, bint ignore_missing_currency_data)
