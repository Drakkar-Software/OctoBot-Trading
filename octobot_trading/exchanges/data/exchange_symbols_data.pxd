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
from octobot_trading.exchanges.abstract_exchange cimport AbstractExchange
from octobot_trading.exchanges.data.exchange_symbol_data cimport ExchangeSymbolData
from octobot_trading.exchanges.exchange_manager cimport ExchangeManager

cdef class ExchangeSymbolsData:
    cdef public object logger

    cdef public dict exchange_symbol_data
    cdef public dict config

    cdef public AbstractExchange exchange
    cdef public ExchangeManager exchange_manager

    cpdef public ExchangeSymbolData get_exchange_symbol_data(self, str symbol, bint allow_creation=*)
