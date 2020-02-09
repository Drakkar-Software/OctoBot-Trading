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
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
from octobot_trading.util.initializable cimport Initializable


cdef class PricesManager(Initializable):
    cdef object logger

    cdef public object prices_initialized_event

    cdef public double mark_price

    cdef void __reset_prices(self)

    cpdef list set_mark_price(self, double mark_price)

    @staticmethod
    cdef double calculate_mark_price_from_recent_trade_prices(list recent_trade_prices)
