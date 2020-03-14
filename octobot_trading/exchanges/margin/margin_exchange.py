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
import ccxt

from octobot_trading.exchanges.rest_exchange import RestExchange


class MarginExchange(RestExchange):
    """
    CCXT margin library wrapper
    """
    async def get_symbol_open_positions(self, symbol: str) -> dict:
        raise NotImplementedError("get_symbol_open_positions is not implemented")

    async def get_open_positions(self) -> dict:
        raise NotImplementedError("get_open_positions is not implemented")

    async def get_symbol_positions_history(self, symbol: str):
        raise NotImplementedError("get_symbol_positions_history is not implemented")

    async def get_positions_history(self):
        raise NotImplementedError("get_positions_history is not implemented")

    async def get_symbol_leverage(self, symbol: str):
        raise NotImplementedError("get_symbol_leverage is not implemented")

    async def set_symbol_leverage(self, symbol: str, leverage: int):
        raise NotImplementedError("set_symbol_leverage is not implemented")

    async def set_symbol_margin_type(self, symbol: str, isolated: bool):
        # If not isolated = cross
        raise NotImplementedError("set_symbol_margin_type is not implemented")

    def cleanup_position_dict(self, position) -> dict:
        return position
