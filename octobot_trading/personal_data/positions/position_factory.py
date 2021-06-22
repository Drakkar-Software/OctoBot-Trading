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
import octobot_trading.personal_data as personal_data
import octobot_trading.enums as enums


def create_position_instance_from_raw(trader, raw_position):
    """
    Creates a position instance from a raw position dictionary
    :param trader: the trader instance
    :param raw_position: the raw position dictionary
    :return: the created position
    """
    position_type = personal_data.parse_position_type(raw_position)
    position = create_position_from_type(trader, position_type)
    position.update_from_raw(raw_position)
    return position


def create_position_from_type(trader, position_type):
    """
    Creates a position instance from a position type
    :param trader: the trader instance
    :param position_type: the position type, a enums.TraderPositionType value
    :return: the created position
    """
    return personal_data.TraderPositionTypeClasses[position_type](trader)


def create_symbol_position(trader, symbol):
    """
    Creates a position for a specified symbol
    :param trader: the trader instance
    :param symbol: the position symbol
    :return: the created position
    """
    return create_position_instance_from_raw(trader, {
        enums.ExchangeConstantsPositionColumns.SYMBOL.value: symbol
    })
