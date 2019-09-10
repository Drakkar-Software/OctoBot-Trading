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
from octobot_commons.logging.logging_util import get_logger

from octobot_trading.util.initializable import Initializable


class TimeManager(Initializable):
    def __init__(self, config, exchange_manager):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.config, self.exchange_manager = config, exchange_manager
        self.time_initialized = False  # TODO
        self.timestamp = 0

    async def initialize_impl(self):
        self._reset_time()
        self.time_initialized = True

    def _reset_time(self):
        self.timestamp = 0

    def set_timestamp(self, timestamp):
        self.timestamp = timestamp
