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
import time
from octobot_commons.logging.logging_util import get_logger
from octobot_trading.constants import DEFAULT_EXCHANGE_TIME_LAG
from octobot_trading.util.initializable import Initializable


class AbstractExchange(Initializable):
    def __init__(self, config, exchange_type, exchange_manager):
        super().__init__()
        self.config = config
        self.exchange_type = exchange_type
        self.exchange_manager = exchange_manager
        self.name = self.exchange_type.__name__
        self.logger = get_logger(f"{self.__class__.__name__}[{self.name}]")
        self.allowed_time_lag = DEFAULT_EXCHANGE_TIME_LAG

    async def initialize_impl(self):
        raise NotImplementedError("initialize_impl not implemented")

    def get_exchange_current_time(self):
        return time.time()

    @classmethod
    def get_name(cls) -> str:
        raise NotImplementedError("get_name is not implemented")
