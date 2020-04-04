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
from octobot_trading.exchanges.rest_exchange cimport RestExchange

cdef class FutureExchange(RestExchange):
    cpdef dict parse_position(self, dict position_dict)
    cpdef dict parse_funding(self, dict funding_dict, bint from_ticker=*)
    cpdef dict parse_mark_price(self, dict mark_price_dict, bint from_ticker=*)
    cpdef dict parse_liquidation(self, dict liquidation_dict)
    cpdef str parse_position_status(self, str status)
    cpdef str parse_position_side(self, str side)
    cpdef double calculate_position_value(self, double quantity, double mark_price)
