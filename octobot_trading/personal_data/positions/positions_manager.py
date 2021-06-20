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
import collections

import octobot_commons.logging as logging

import octobot_trading.util as util
import octobot_trading.personal_data.positions.position_factory as position_factory
import octobot_trading.personal_data.positions.position as position_class


class PositionsManager(util.Initializable):
    def __init__(self, trader):
        super().__init__()
        self.logger = logging.get_logger(self.__class__.__name__)
        self.trader = trader
        self.positions_initialized = False  # TODO
        self.positions = collections.OrderedDict()

    async def initialize_impl(self):
        self._reset_positions()

    def get_symbol_position(self, symbol):
        return self._select_positions(symbol=symbol)

    def get_position_by_id(self, position_id):
        return self.positions.get(position_id, None)

    async def upsert_position(self, position_id, raw_position) -> bool:
        if position_id not in self.positions:
            new_position = position_factory.create_position_instance_from_raw(self.trader, raw_position)
            self.positions[position_id] = new_position
            await new_position.initialize(is_from_exchange_data=True)
            return True

        return self._update_position_from_raw(self.positions[position_id], raw_position)

    def upsert_position_instance(self, position) -> bool:
        if position.position_id not in self.positions:
            self.positions[position.position_id] = position
            return True
        # TODO
        return False

    # private
    def _create_position_from_raw(self, raw_position):
        position = position_class.Position(self.trader)
        position.update_from_raw(raw_position)
        return position

    def _update_position_from_raw(self, position, raw_position):
        return position.update_from_raw(raw_position)

    def _select_positions(self, symbol=None):
        if symbol is None:
            return self.positions
        for position in self.positions:
            if position.symbol == symbol:
                return position
        return None

    def _reset_positions(self):
        self.positions_initialized = False
        self.positions = collections.OrderedDict()
