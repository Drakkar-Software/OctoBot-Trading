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

from octobot_trading.data_manager.time_manager import TimeManager
from octobot_trading.util.initializable import Initializable


class ExchangeGlobalData(Initializable):
    def __init__(self, exchange_manager):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.exchange_manager = exchange_manager
        self.config = exchange_manager.config

        self.time_manager = None

    async def initialize_impl(self):
        try:
            self.time_manager = TimeManager(self.config, self.exchange_manager)
        except Exception as e:
            self.logger.error(f"Error when initializing : {e}. "
                              f"{self.exchange.name} global data disabled.")
            self.logger.exception(e)

    async def handle_time_update(self, timestamp):
        # TODO check if initialized
        return self.time_manager.set_timestamp(timestamp)
