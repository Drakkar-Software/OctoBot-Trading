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
cimport octobot_backtesting.backtesting as backtesting
cimport octobot_trading.exchanges.abstract_exchange as abstract_exchange

cdef class ExchangeSimulator(abstract_exchange.AbstractExchange):
    cdef public backtesting.Backtesting backtesting

    cdef public list exchange_importers

    cdef public dict current_future_candles

    cdef public bint is_authenticated

    cpdef str get_pair_cryptocurrency(self, str pair)
    cpdef list get_available_time_frames(self)
    cpdef list get_time_frames(self, object importer)

# Should be cythonized with cython 3.0
# cpdef set handles_real_data_for_updater(str channel_type, list available_data_types)

# Should be cythonized with cython 3.0
# cdef bint _are_required_data_available(str channel_type, list available_data_types)
