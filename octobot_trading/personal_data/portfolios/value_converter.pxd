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


cimport octobot_trading.personal_data.portfolios.portfolio_manager as portfolio_manager

cdef class ValueConverter:
    cdef public portfolio_manager.PortfolioManager portfolio_manager
    cdef object _bot_main_loop
    cdef object logger
    cdef object config

    cdef public dict last_prices_by_trading_pair

    cdef public set initializing_symbol_prices
    cdef public set initializing_symbol_prices_pairs

    cdef public set missing_currency_data_in_exchange

    cdef dict _price_bridge_by_symbol
    cdef set _missing_price_bridges

    cpdef void update_last_price(self, str symbol, object price)
    cpdef object evaluate_value(self, str currency, object quantity, bint raise_error=*)
    cpdef object convert_currency_value_using_last_prices(self, object quantity, str current_currency, str target_currency, str settlement_asset=*)
    cpdef object try_convert_currency_value_using_multiple_pairs(self, str currency, str target, object quantity, list base_bridge)
    cpdef list get_saved_price_conversion_bridge(self, str currency, str target)
    cpdef object convert_currency_value_from_saved_price_bridges(self, str currency, str target, object quantity)
    cpdef void reset_missing_price_bridges(self)
    cpdef bint is_missing_price_bridge(self, str base, str quote)
    cpdef void clear(self)

    cdef object _check_currency_initialization(self, str currency, object currency_value)
    cdef void _try_to_ask_ticker_missing_symbol_data(self, str currency, str symbol, str reversed_symbol)
    cdef void _ask_ticker_data_for_currency(self, list symbols_to_add)
    cdef void _inform_no_matching_symbol(self, str currency)
    cdef void _remove_from_missing_currency_data(self, str currency)
    cdef object _has_price_data(self, str symbol) # return object to propagate exceptions
    cdef object _get_last_price_data(self, str symbol)
    cdef object _ensure_no_pending_symbol_price(self, str base, str quote)
    cdef void _save_price_bridge(self, str currency, str target, list bridge)
    cdef void _save_missing_price_bridge(self, str base, str quote)
