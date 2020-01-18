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
from octobot_trading.traders.trader cimport Trader

cdef class ExchangeFactory:
    cdef public ExchangeManager exchange_manager

    cdef dict config

    cdef object logger

    cdef Trader trader

    cdef list backtesting_files

    cdef public str exchange_name

    cdef bint is_simulated
    cdef bint is_backtesting
    cdef bint ignore_config
    cdef bint is_sandboxed
    cdef bint rest_only
    cdef bint is_collecting
    cdef bint exchange_only
    cdef str matrix_id
