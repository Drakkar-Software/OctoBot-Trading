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
cimport octobot_trading.util as util

cdef class ExchangeConfig(util.Initializable):
    cdef object _logger

    cdef public dict traded_cryptocurrencies
    cdef public dict config

    cdef public list traded_symbol_pairs
    cdef public list all_config_symbol_pairs
    cdef public list traded_time_frames
    cdef public list real_time_time_frames

    cdef public object exchange_manager

    cpdef void set_config_time_frame(self)
    cpdef void set_config_traded_pairs(self)
    cpdef object get_shortest_time_frame(self)

    @staticmethod
    cdef str _is_tradable_with_cryptocurrency(str symbol, str cryptocurrency)

    cdef void _set_config_time_frame(self)
    cdef void _set_config_traded_pairs(self)
    cdef void _populate_non_wildcard_pairs(self, str cryptocurrency, set existing_pairs, bint is_enabled)
    cdef void _populate_wildcard_pairs(self, str cryptocurrency, set existing_pairs, bint is_enabled)
    cdef list _add_tradable_symbols_from_config(self, str cryptocurrency, list filtered_symbols)
    cdef object _add_tradable_symbols(self, str cryptocurrency, list symbols)
    cdef list _add_tradable_time_frames(self, list time_frames)
    cdef list _create_wildcard_symbol_list(self, str cryptocurrency)
