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

from octobot_trading.channels.time import TimeProducer


class TimeUpdater(TimeProducer):
    TIME_INTERVAL = 1

    def __init__(self, channel):
        super().__init__(channel)
        self.starting_timestamp = None
        self.current_timestamp = None

    def set_minimum_timestamp(self, minimum_timestamp):
        if self.starting_timestamp is None or self.starting_timestamp > minimum_timestamp:
            self.starting_timestamp = minimum_timestamp
            self.logger.info(f"Set minimum timestamp to : {minimum_timestamp}")

    async def start(self):
        if self.starting_timestamp is None:
            self.starting_timestamp = time.time()
        self.current_timestamp = self.starting_timestamp

        while not self.should_stop:
            try:
                await self.push(timestamp=self.current_timestamp)
                self.current_timestamp += self.TIME_INTERVAL
                await self.wait_for_processing()
            except Exception as e:
                self.logger.exception(f"Fail to update time : {e}")

    async def modify(self, set_timestamp=None, minimum_timestamp=None) -> None:
        if set_timestamp is not None:
            self.current_timestamp = set_timestamp
            self.logger.info(f"Set timestamp to : {set_timestamp}")

        if minimum_timestamp is not None:
            self.set_minimum_timestamp(minimum_timestamp)
            self.current_timestamp = minimum_timestamp
