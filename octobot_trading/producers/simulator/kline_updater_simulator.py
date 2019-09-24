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
import json

from octobot_channels.channels.channel import get_chan

from octobot_commons.channels_name import OctoBotBacktestingChannelsName
from octobot_commons.enums import TimeFrames
from octobot_trading.producers.kline_updater import KlineUpdater


class KlineUpdaterSimulator(KlineUpdater):
    def __init__(self, channel, importer):
        super().__init__(channel)
        self.exchange_data_importer = importer
        self.exchange_name = self.channel.exchange_manager.exchange.name

        self.last_timestamp_pushed = 0
        self.time_consumer = None

    async def start(self):
        await self.resume()

    async def handle_timestamp(self, timestamp: int):
        try:
            # TODO foreach symbol and time_frame
            kline_data = (await self.exchange_data_importer.get_kline_from_timestamps(exchange_name=self.exchange_name,
                                                                                      symbol="BTC/USDT",
                                                                                      time_frame="1h",
                                                                                      inferior_timestamp=timestamp,
                                                                                      limit=1))[0]
            if kline_data[0] > self.last_timestamp_pushed:
                self.last_timestamp_pushed = kline_data[0]
                await self.push(TimeFrames(kline_data[-2]), kline_data[3], json.loads(kline_data[-1]))
        except IndexError as e:
            self.logger.warning(f"Failed to access kline_data : {e}")

    async def pause(self, **kwargs) -> None:
        if self.time_consumer is not None:
            await get_chan(OctoBotBacktestingChannelsName.TIME_CHANNEL.value).remove_consumer(self.time_consumer)

    async def resume(self, **kwargs) -> None:
        if self.time_consumer is None and not self.channel.is_paused:
            self.time_consumer = await get_chan(OctoBotBacktestingChannelsName.TIME_CHANNEL.value).new_consumer(
                self.handle_timestamp)
