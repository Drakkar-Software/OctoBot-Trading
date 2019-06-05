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

from octobot_trading.traders.trader cimport Trader
from octobot_trading.exchanges.backtesting.exchange_simulator cimport ExchangeSimulator

cdef class Backtesting:
    cdef public object config
    cdef public float begin_time
    cdef public bint force_exit_at_end
    cdef ExchangeSimulator exchange_simulator
    cdef public set ended_symbols
    cdef public set symbols_to_test

    cdef object logger

    cpdef void print_trades_history(self)
    cpdef Trader get_trader(self)

    cdef void _init_symbols_to_test(self)
