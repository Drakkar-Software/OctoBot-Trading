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
from octobot_trading.exchanges.exchange_manager cimport ExchangeManager
from octobot_trading.util.initializable cimport Initializable

cdef class ExchangeConfig(Initializable):
    cdef public object logger

    cdef public dict traded_cryptocurrencies_pairs
    cdef public list traded_symbol_pairs
    cdef public list traded_time_frames

    cdef public dict config

    cdef public ExchangeManager exchange_manager

    cpdef void set_config_time_frame(self)
    cpdef void set_config_traded_pairs(self)
    cpdef list get_traded_pairs(self, str crypto_currency=*)

    cdef void __set_config_time_frame(self)
    cdef void __set_config_traded_pairs(self)
    cdef list __add_tradable_symbols_from_config(self, str crypto_currency)
    cdef object __add_tradable_symbols(self, str crypto_currency, list symbols)
    cdef list __add_tradable_time_frames(self, list time_frames)
