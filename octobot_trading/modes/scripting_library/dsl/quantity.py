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
import decimal
import re

import octobot_trading.modes.scripting_library.dsl.values as dsl_values


QUANTITY_REGEX = r"-?\d|\."


def parse_quantity(input_offset) -> (dsl_values.QuantityType, decimal.Decimal):
    input_offset = input_offset or ""
    input_offset = str(input_offset)
    try:
        quantity_type, value = dsl_values.QuantityType.parse(re.sub(QUANTITY_REGEX, "", input_offset))
        offset_value = None if input_offset == value else decimal.Decimal(input_offset.replace(value, ""))
        return quantity_type, offset_value
    except ValueError:
        return dsl_values.QuantityType.UNKNOWN, None
