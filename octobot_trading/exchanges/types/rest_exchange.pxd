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

cdef class RestExchange(abstract_exchange.AbstractExchange):
    cdef public dict pair_contracts

    cpdef object get_adapter_class(self)
    cpdef contracts.FutureContract create_pair_contract(
            self, str pair,
            object current_leverage, object contract_size, object margin_type,
            object contract_type, object position_mode,
            object maintenance_margin_rate,
            object maximum_leverage=*
    )
    cpdef contracts.FutureContract get_pair_future_contract(self, str pair)
    cpdef void set_pair_future_contract(self, str pair, contracts.FutureContract future_contract)
    cpdef bint is_linear_symbol(self, str symbol)
    cpdef bint is_inverse_symbol(self, str symbol)
    cpdef bint supports_trading_type(self, str symbol, object trading_type)

    """
    Parsers
    """
    cpdef dict parse_funding(self, dict funding_dict, bint from_ticker=*)
    cpdef dict parse_mark_price(self, dict mark_price_dict, bint from_ticker=*)

    cdef object _create_connector(self, dict config, object exchange_manager, object connector_class)
