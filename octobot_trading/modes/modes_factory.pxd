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

cdef list _get_cryptocurrencies_to_create(object trading_mode_class, dict cryptocurrencies)
cdef list _get_symbols_to_create(object trading_mode_class,
                                 dict cryptocurrencies,
                                 str cryptocurrency,
                                 list symbols)
cdef list _get_time_frames_to_create(object trading_mode_class, list time_frames)
