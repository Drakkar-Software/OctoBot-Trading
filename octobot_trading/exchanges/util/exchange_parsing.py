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


def set_exchange_value_if_necessary(parsed_dict, default_key, exchange_key):
    if default_key not in parsed_dict and exchange_key in parsed_dict:
        parsed_dict[default_key] = parsed_dict[exchange_key]


def set_exchange_value_to_default(parsed_dict, default_key, default_value):
    if default_key not in parsed_dict:
        parsed_dict[default_key] = default_value


def calculate_position_value(quantity, mark_price):
    if mark_price:
        return quantity / mark_price
    return 0
