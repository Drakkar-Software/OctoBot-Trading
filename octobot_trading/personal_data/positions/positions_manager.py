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
import asyncio
import collections

import octobot_commons.logging as logging

import octobot_trading.personal_data.positions.position_factory as position_factory
import octobot_trading.util as util


class PositionsManager(util.Initializable):
    def __init__(self, trader):
        super().__init__()
        self.logger = logging.get_logger(self.__class__.__name__)
        self.trader = trader
        self.positions_initialized = False
        self.positions = collections.OrderedDict()

    async def initialize_impl(self):
        self._reset_positions()

    def get_symbol_position(self, symbol):
        return self._select_positions(symbol=symbol)

    def get_position_by_id(self, position_id):
        return self.positions.get(position_id, None)

    def get_symbol_leverage(self, symbol):
        return self._select_positions(symbol=symbol).leverage

    def get_symbol_margin_type(self, symbol):
        return self._select_positions(symbol=symbol).margin_type

    async def upsert_position(self, position_id, raw_position) -> bool:
        """
        Create or update a position from a raw dictionary
        :param position_id: the position id
        :param raw_position: the position raw dictionary
        :return: True when the creation or the update succeeded
        """
        if position_id not in self.positions:
            new_position = position_factory.create_position_instance_from_raw(self.trader, raw_position)
            return await self._finalize_position_creation(new_position, is_from_exchange_data=True)

        return self.positions[position_id].update_from_raw(raw_position)

    async def recreate_position(self, position) -> bool:
        """
        Recreate position from an existing position instance
        :param position: the position instance to recreate
        :return: True when the recreation succeeded
        """
        new_position = position_factory.create_position_instance_from_raw(self.trader, position.to_dict())
        position.clear()
        return await self._finalize_position_creation(new_position)

    def upsert_position_instance(self, position) -> bool:
        """
        Save an existing position instance to positions list
        :param position: the position instance
        :return: True when the operation succeeded
        """
        if position.position_id not in self.positions:
            self.positions[position.position_id] = position
            return True
        # TODO
        return False

    def clear(self):
        """
        Clear all positions and the position OrderedDict
        """
        for position in self.positions.values():
            position.clear()
        self._reset_positions()

    # private
    async def _finalize_position_creation(self, new_position, is_from_exchange_data=False) -> bool:
        """
        Ends a position creation process
        :param new_position: the new position instance
        :param is_from_exchange_data: True when the exchange creation comes from exchange data
        :return: True when the process succeeded
        """
        self.positions[new_position.position_id] = new_position
        await new_position.initialize(is_from_exchange_data=is_from_exchange_data)
        return True

    def _create_symbol_position(self, symbol):
        """
        Creates a position when it doesn't exist for the specified symbol
        :return: the new symbol position instance
        """
        new_position = position_factory.create_symbol_position(self.trader, symbol)
        asyncio.create_task(self._finalize_position_creation(new_position))
        return new_position

    def _select_positions(self, symbol=None):
        """
        Filter positions by symbol
        :param symbol: the symbol to match, all symbol are considered when symbol is None
        :return: positions matching the symbol selector
        """
        if symbol is None:
            return self.positions
        for position in self.positions.values():
            if position.symbol == symbol:
                return position
        return self._create_symbol_position(symbol)

    def _reset_positions(self):
        """
        Clear all position references
        """
        self.positions_initialized = False
        self.positions = collections.OrderedDict()
