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

from octobot_backtesting.data import DataBaseNotExists
from octobot_channels.channels.channel import get_chan
from octobot_commons.channels_name import OctoBotBacktestingChannelsName

from octobot_commons.enums import TimeFrames

from octobot_trading.producers.ohlcv_updater import OHLCVUpdater


class OHLCVUpdaterSimulator(OHLCVUpdater):
    def __init__(self, channel, importer):
        super().__init__(channel)
        self.exchange_data_importer = importer
        self.exchange_name = self.channel.exchange_manager.exchange_name

        self.last_timestamp_pushed = 0
        self.time_consumer = None

    async def start(self):
        await self.resume()

    async def handle_timestamp(self, timestamp, **kwargs):
        if self.last_timestamp_pushed == 0:
            self.last_timestamp_pushed = timestamp

        try:
            for time_frame in self.channel.exchange_manager.exchange_config.traded_time_frames:
                for pair in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
                    ohlcv_data: list = await self.exchange_data_importer.get_ohlcv_from_timestamps(
                        exchange_name=self.exchange_name,
                        symbol=pair,
                        time_frame=time_frame,
                        inferior_timestamp=self.last_timestamp_pushed,
                        superior_timestamp=timestamp)

                    if ohlcv_data:
                        await self.push(time_frame, pair, [ohlcv[-1] for ohlcv in ohlcv_data], partial=True)

            self.last_timestamp_pushed = timestamp
        except DataBaseNotExists as e:
            self.logger.warning(f"Not enough data : {e}")
            await self.pause()
            await self.stop()
        except IndexError as e:
            self.logger.warning(f"Failed to access ohlcv_data : {e}")

    async def pause(self):
        if self.time_consumer is not None:
            await get_chan(OctoBotBacktestingChannelsName.TIME_CHANNEL.value).remove_consumer(self.time_consumer)

    async def resume(self):
        if self.time_consumer is None and not self.channel.is_paused:
            self.time_consumer = await get_chan(OctoBotBacktestingChannelsName.TIME_CHANNEL.value).new_consumer(
                self.handle_timestamp)
