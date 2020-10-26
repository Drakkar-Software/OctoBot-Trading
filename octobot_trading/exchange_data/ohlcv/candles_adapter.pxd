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
cimport numpy as np
np.import_array()

cimport octobot_trading.exchange_data.exchange_symbol_data as exchange_symbol_data

cpdef np.ndarray get_symbol_close_candles(exchange_symbol_data.ExchangeSymbolData symbol_data, str time_frame,  int limit, bint include_in_construction)
cpdef np.ndarray get_symbol_open_candles(exchange_symbol_data.ExchangeSymbolData symbol_data, str time_frame, int limit, bint include_in_construction)
cpdef np.ndarray get_symbol_high_candles(exchange_symbol_data.ExchangeSymbolData symbol_data, str time_frame, int limit, bint include_in_construction)
cpdef np.ndarray get_symbol_low_candles(exchange_symbol_data.ExchangeSymbolData symbol_data, str time_frame, int limit, bint include_in_construction)
cpdef np.ndarray get_symbol_volume_candles(exchange_symbol_data.ExchangeSymbolData symbol_data, str time_frame, int limit, bint include_in_construction)
cpdef np.ndarray get_symbol_time_candles(exchange_symbol_data.ExchangeSymbolData symbol_data, str time_frame, int limit, bint include_in_construction)

cdef np.ndarray _add_in_construction_data(np.ndarray candles, exchange_symbol_data.ExchangeSymbolData symbol_data, object time_frame, int data_type)