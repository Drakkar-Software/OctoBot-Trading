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
from math import nan

from octobot_commons.logging.logging_util import get_logger
from octobot_trading.util.initializable import Initializable


class FundingManager(Initializable):
    def __init__(self):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.funding_rate = nan
        self.next_updated = 0
        self.last_updated = 0
        self.reset_funding()

    async def initialize_impl(self):
        self.reset_funding()

    def reset_funding(self):
        self.funding_rate = nan
        self.next_updated = 0
        self.last_updated = 0

    def funding_update(self, funding_rate, next_funding_time, timestamp):
        if funding_rate and next_funding_time:
            self.funding_rate = funding_rate
            self.next_updated = next_funding_time
            self.last_updated = timestamp
