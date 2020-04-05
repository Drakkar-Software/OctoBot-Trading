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

cdef class ExchangeBuilder:
    cdef object logger

    cdef dict config

    cdef public ExchangeManager exchange_manager

    cdef public str exchange_name

    cdef bint _is_using_trading_modes

    cdef str _matrix_id

    cdef object _tentacles_setup_config

    """
    Builder methods
    """
    cpdef ExchangeBuilder is_backtesting(self, list backtesting_files)
    cpdef ExchangeBuilder is_sandboxed(self, bint sandboxed)
    cpdef ExchangeBuilder is_simulated(self)
    cpdef ExchangeBuilder is_collecting(self)
    cpdef ExchangeBuilder is_real(self)
    cpdef ExchangeBuilder is_margin(self, bint use_margin=*)
    cpdef ExchangeBuilder is_exchange_only(self)
    cpdef ExchangeBuilder is_ignoring_config(self)
    cpdef ExchangeBuilder use_tentacles_setup_config(self, object tentacles_setup_config)
    cpdef ExchangeBuilder disable_trading_mode(self)
    cpdef ExchangeBuilder has_matrix(self, str matrix_id)
