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
cimport octobot_trading.exchanges.abstract_exchange as abstract_exchange
cimport octobot_trading.exchange_data.contracts as contracts

cdef class FutureExchange(abstract_exchange.AbstractExchange):
    cdef dict pair_contracts

    cpdef void create_pair_contract(self, str pair,
                                    object current_leverage, object margin_type,
                                    object contract_type, object position_mode,
                                    object maintenance_margin_rate,
                                    object maximum_leverage=*)
    cpdef double calculate_position_value(self, double quantity, double mark_price)
    cpdef contracts.FutureContract get_pair_future_contract(self, str pair)
    cpdef void set_pair_future_contract(self, str pair, contracts.FutureContract future_contract)
    cpdef bint is_linear_symbol(self, str symbol)
    cpdef bint is_inverse_symbol(self, str symbol)
    cpdef bint is_futures_symbol(self, str symbol)

    """
    Parsers
    """
    cpdef list parse_positions(self, list positions)
    cpdef dict parse_position(self, dict position_dict)
    cpdef dict parse_funding(self, dict funding_dict, bint from_ticker=*)
    cpdef dict parse_mark_price(self, dict mark_price_dict, bint from_ticker=*)
    cpdef dict parse_liquidation(self, dict liquidation_dict)
    cpdef object parse_position_status(self, str status)
    cpdef object parse_position_side(self, str side)
