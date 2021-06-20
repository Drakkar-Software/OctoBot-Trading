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
import octobot_trading.enums as enums


async def create_position_state(position, is_from_exchange_data=False, ignore_states=None):
    if ignore_states is None:
        ignore_states = []

    if position.status is enums.PositionStatus.OPEN and enums.States.OPEN not in ignore_states:
        await position.on_open(force_open=False, is_from_exchange_data=is_from_exchange_data)
    elif position.status is enums.PositionStatus.LIQUIDATING and enums.PositionStates.LIQUIDATED not in ignore_states:
        await position.on_liquidate(force_liquidate=False, is_from_exchange_data=is_from_exchange_data)
