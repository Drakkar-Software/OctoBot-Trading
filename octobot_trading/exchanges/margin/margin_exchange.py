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

from octobot_trading.exchanges.rest_exchange import RestExchange


class MarginExchange(RestExchange):
    """
    CCXT margin library wrapper
    """

    def __init__(self, config, exchange_type, exchange_manager):
        super().__init__(config, exchange_type, exchange_manager)

    async def get_position(self, params={}):
        raise NotImplementedError("get_position")

    async def get_open_position(self):
        raise NotImplementedError("get_open_position")

    async def get_position_from_id(self, position_id, symbol=None):
        raise NotImplementedError("get_position_from_id")

    async def get_positions(self, symbol=None, since=None, limit=None, params={}):
        raise NotImplementedError("get_positions")

    async def get_open_positions(self, symbol=None, since=None, limit=None, params={}):
        raise NotImplementedError("get_open_positions")

    async def get_closed_positions(self, symbol=None, since=None, limit=None, params={}):
        raise NotImplementedError("get_closed_positions")

    async def get_position_trades(self, position_id, symbol=None, since=None, limit=None, params={}):
        raise NotImplementedError("get_position_trades")

    async def get_position_status(self, position_id, symbol=None, params={}):
        raise NotImplementedError("get_position_status")