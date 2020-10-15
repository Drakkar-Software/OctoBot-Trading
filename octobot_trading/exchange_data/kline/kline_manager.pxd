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


cdef class KlineManager(util.Initializable):
    cdef object logger

    cdef public list kline

    cdef void _reset_kline(self)
    cdef void _update_kline_key(self, int kline_key, list kline_update)
    cdef void _update_kline_init_only_key(self, int kline_key, list kline_update)

    cpdef void kline_update(self, list kline)
