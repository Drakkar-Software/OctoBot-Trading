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

import re


def target_position(target, current_symbol_holding):
    target_position_type = re.sub(r"\d|\.", "", target)
    target_position_value = float(target.replace(target_position_type, ""))

    current_position_size = None # todo

    if target_position_type == "%p":
        target_size = current_position_size * target_position_value / 100
        order_size = target_size - current_position_size
        return order_size
    if target_position_type == "":
        order_size = target_position_value - current_position_size
        return order_size
    if target_position_type == "%":
        current_account_balance = None # todo needs to be converted to contract size
        target_size = current_account_balance * target_position_value / 100
        order_size = target_size - current_position_size
        return order_size

    if target_position_type == "%a":
        current_available_account_balance =  None # todo needs to be converted to contract size
        target_size = current_available_account_balance * target_position_value / 100
        order_size = target_size - current_available_account_balance
        return order_size

    else:
        raise RuntimeError("make sure to use a supported syntax for position")


def target_position_side(ordersize):
    if ordersize <= 0:
        return "sell"
    if ordersize >= 0:
        return "buy"
