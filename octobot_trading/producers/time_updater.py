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
    TIME_INTERVAL = 0.1

    def __init__(self, channel):
        super().__init__(channel)
        self.current_timestamp = time.time()

    async def start(self):
        while not self.should_stop:
            try:
                await self.push(timestamp=self.current_timestamp)
                self.current_timestamp += self.TIME_INTERVAL
                await self.wait_for_processing()
            except Exception as e:
                self.logger.exception(f"Fail to update time : {e}")
