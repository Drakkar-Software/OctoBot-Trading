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

async def get_target_position(
        target=None,
        context=None
):
    target = str(target)
    target_position_type = re.sub(r"\d|\.", "", target)
    target_position_value = decimal.Decimal(target.replace(target_position_type, ""))
    order_size = None

    if target_position_type == "%p":
        open_position_size_val = await open_position_size(context)
        target_size = open_position_size_val * target_position_value / 100
        order_size = target_size - open_position_size_val

    elif target_position_type == "%":
        total_acc_bal = await total_account_balance(context)
        target_size = total_acc_bal * target_position_value / 100
        order_size = target_size - await open_position_size(context)

    elif target_position_type == "":
        order_size = target_position_value - await open_position_size(context)

    elif target_position_type == "%a":
        available_account_balance_val = await available_account_balance(context)
        target_size = available_account_balance_val * target_position_value / 100
        order_size = target_size - available_account_balance_val

    elif True:
        raise RuntimeError("make sure to use a supported syntax for position")

    side = None
    if order_size < 0:
        side = "sell"
        order_size = order_size * -1
    elif order_size > 0:
        side = "buy"
    elif order_size == 0:
        raise RuntimeError("Computed position Size is 0")

    order_size = await cut_position_size(context, order_size, side)
    return order_size, side


def target_position_side(ordersize):
    if ordersize <= 0:
        return "sell"
    if ordersize >= 0:
        return "buy"
