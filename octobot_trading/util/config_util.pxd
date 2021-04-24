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


cpdef bint is_trader_enabled(dict config)
cpdef bint is_trader_simulator_enabled(dict config)
cpdef bint is_currency_enabled(dict config, str currency, bint default_value)
cpdef bint is_trade_history_loading_enabled(dict config, bint default=*)
cpdef list get_symbols(dict config, bint enabled_only)
cpdef set get_all_currencies(dict config, bint enabled_only=*)
cpdef list get_pairs(dict config, str currency, bint enabled_only=*)
cpdef tuple get_market_pair(dict config, str currency, bint enabled_only=*)
cpdef str get_reference_market(dict config)
cpdef dict get_traded_pairs_by_currency(dict config)

cdef bint _is_trader_enabled(dict config, str trader_key)
