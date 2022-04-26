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

import enum


class QuantityType(enum.Enum):
    DELTA = ""
    PERCENT = "%"
    AVAILABLE = "a"
    POSITION = "p"
    ENTRY = "e"
    AVAILABLE_PERCENT = "a%"
    POSITION_PERCENT = "p%"
    ENTRY_PERCENT = "e%"
    FLAT = "@"
    UNKNOWN = "?"

    @staticmethod
    def parse(value):
        try:
            # try reading directly as enum
            return QuantityType(value), value
        except ValueError:
            # try with letters in reverse order
            reversed_value = value[::-1]
            return QuantityType(reversed_value), value
