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
from collections import OrderedDict

from octobot_commons.logging.logging_util import get_logger

from octobot_trading.data.position import Position
from octobot_trading.enums import PositionStatus
from octobot_trading.util.initializable import Initializable


class PositionsManager(Initializable):
    MAX_POSITIONS_COUNT = 2000

    def __init__(self, config, trader, exchange_manager):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.config, self.trader, self.exchange_manager = config, trader, exchange_manager
        self.positions_initialized = False  # TODO
        self.positions = OrderedDict()

    async def initialize_impl(self):
        self._reset_positions()

    def get_open_positions(self, symbol=None, since=-1, limit=-1):
        return self._select_positions(True, symbol, since, limit)

    def get_closed_positions(self, symbol=None, since=-1, limit=-1):
        return self._select_positions(False, symbol, since, limit)

    def upsert_position(self, position_id, raw_position) -> bool:
        if position_id not in self.positions:
            self.positions[position_id] = self._create_position_from_raw(raw_position)
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
        position = Position(self.trader)
        position.update_position_from_raw(raw_position)
        return position

    def _update_position_from_raw(self, position, raw_position):
        return position.update_position_from_raw(raw_position)

    def _select_positions(self, status=PositionStatus.OPEN, symbol=None, since=-1, limit=-1):
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
        self.positions = OrderedDict()

    def _remove_oldest_positions(self, nb_to_remove):
        for _ in range(nb_to_remove):
            self.positions.popitem(last=False)
