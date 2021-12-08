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

from octobot_trading.modes.scripting_library.data.reading.exchange_private_data.account_balance import *
from octobot_trading.modes.scripting_library.data.reading.exchange_private_data.open_positions import *
from octobot_trading.modes.scripting_library.orders.position_size.cut_position_size import *


async def get_amount(input_amount=None,
                     context=None,
                     side="buy"
                     ):
    input_amount = str(input_amount)
    amount_type = re.sub(r"\d|\.", "", input_amount)
    amount_value = decimal.Decimal(input_amount.replace(amount_type, ""))

    if amount_value <= 0:
        raise RuntimeError("amount cant be zero or negative")

    if amount_type == "":
        return await cut_position_size(context, amount_value, side)

    elif amount_type == "%":
        amount_value = total_account_balance(context, side) * amount_value / 100
        return await cut_position_size(context, amount_value, side)

    elif amount_type == "%a":
        amount_value = await available_account_balance(context, side) * amount_value / 100
        return await cut_position_size(context, amount_value, side)

    elif amount_type == "%p":
        amount_value = await open_position_size(context, side) * amount_value / 100
        return await cut_position_size(context, amount_value, side)

    else:
        raise RuntimeError("make sure to use a supported syntax for amount")
