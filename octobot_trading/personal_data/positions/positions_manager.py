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

import octobot_trading.enums as enums
import octobot_trading.util as util
import octobot_trading.personal_data.positions.position_factory as position_factory
import octobot_trading.personal_data.positions.position as position_class


class PositionsManager(util.Initializable):
    MAX_POSITIONS_COUNT = 2000

    def __init__(self, trader):
        super().__init__()
        self.logger = logging.get_logger(self.__class__.__name__)
        self.trader = trader
        self.positions_initialized = False  # TODO
        self.positions = collections.OrderedDict()

    async def initialize_impl(self):
        self._reset_positions()

    def get_symbol_open_position(self, symbol):
        return self.get_open_positions(symbol=symbol)

    def get_open_positions(self, symbol=None, since=-1, limit=-1):
        return self._select_positions(status=enums.PositionStatus.OPEN, symbol=symbol, since=since, limit=limit)

    def get_closed_positions(self, symbol=None, since=-1, limit=-1):
        return self._select_positions(status=enums.PositionStatus.CLOSED, symbol=symbol, since=since, limit=limit)

    def upsert_position(self, position_id, raw_position) -> bool:
        if position_id not in self.positions:
            self.positions[position_id] = position_factory.create_position_instance_from_raw(self.trader, raw_position)
            self._check_positions_size()
            return True

        return self._update_position_from_raw(self.positions[position_id], raw_position)

    def upsert_position_instance(self, position) -> bool:
        if position.position_id not in self.positions:
            self.positions[position.position_id] = position
            self._check_positions_size()
            return True
        # TODO
        return False

    # private
    def _check_positions_size(self):
        if len(self.positions) > self.MAX_POSITIONS_COUNT:
            self._remove_oldest_positions(int(self.MAX_POSITIONS_COUNT / 2))

    def _create_position_from_raw(self, raw_position):
        position = position_class.Position(self.trader)
        position.update_from_raw(raw_position)
        return position

    def _update_position_from_raw(self, position, raw_position):
        return position.update_from_raw(raw_position)

    def _select_positions(self, status=enums.PositionStatus.OPEN, symbol=None, since=-1, limit=-1):
        positions = [
            position
            for position in self.positions.values()
            if (
                    position.status == status and
                    (symbol is None or (symbol and position.symbol == symbol)) and
                    (since == -1 or (since and position.timestamp < since))
            )
        ]
        return positions if limit == -1 else positions[0:limit]

    def _reset_positions(self):
        self.positions_initialized = False
        self.positions = collections.OrderedDict()

    def _remove_oldest_positions(self, nb_to_remove):
        for _ in range(nb_to_remove):
            self.positions.popitem(last=False)
