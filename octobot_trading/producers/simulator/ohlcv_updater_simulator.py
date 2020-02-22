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
import asyncio

from octobot_backtesting.api.backtesting import get_backtesting_current_time
from octobot_backtesting.data import DataBaseNotExists
from octobot_channels.channels.channel import get_chan
from octobot_commons.channels_name import OctoBotBacktestingChannelsName
from octobot_trading.producers.ohlcv_updater import OHLCVUpdater
from octobot_trading.producers.simulator.simulator_updater_utils import stop_and_pause


class OHLCVUpdaterSimulator(OHLCVUpdater):
    def __init__(self, channel, importer):
        super().__init__(channel)
        self.exchange_data_importer = importer
        self.exchange_name = self.channel.exchange_manager.exchange_name

        self.initial_timestamp = get_backtesting_current_time(self.channel.exchange_manager.exchange.backtesting)
        self.last_timestamp_pushed = 0
        self.time_consumer = None

    async def start(self):
        if not self.is_initialized:
            await self._initialize()
        await self.resume()

    async def wait_for_initialization(self, timeout=OHLCVUpdater.OHLCV_INITIALIZATION_TIMEOUT):
        await asyncio.wait_for(self.ohlcv_initialized_event.wait(), timeout)

    async def handle_timestamp(self, timestamp, **kwargs):
        if not self.is_initialized:
            await self.wait_for_initialization()
        if self.last_timestamp_pushed == 0:
            self.last_timestamp_pushed = timestamp

        try:
            for time_frame in self.channel.exchange_manager.exchange_config.traded_time_frames:
                for pair in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
                    # use timestamp - 1 for superior timestamp to avoid select of a future candle
                    # (selection is <= and >=)
                    ohlcv_data: list = await self.exchange_data_importer.get_ohlcv_from_timestamps(
                        exchange_name=self.exchange_name,
                        symbol=pair,
                        time_frame=time_frame,
                        inferior_timestamp=self.last_timestamp_pushed,
                        superior_timestamp=timestamp - 1)
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

    async def stop(self):
        await stop_and_pause(self)

    async def resume(self):
        if self.time_consumer is None and not self.channel.is_paused:
            self.time_consumer = await get_chan(OctoBotBacktestingChannelsName.TIME_CHANNEL.value).new_consumer(
                self.handle_timestamp)

    async def _initialize_candles(self, time_frame, pair):
        # fetch history
        ohlcv_data = None
        try:
            ohlcv_data: list = await self.exchange_data_importer.get_ohlcv_from_timestamps(
                exchange_name=self.exchange_name,
                symbol=pair,
                time_frame=time_frame,
                limit=self.OHLCV_OLD_LIMIT,
                superior_timestamp=self.initial_timestamp - 1)
            self.logger.info(f"Loaded pre-backtesting starting timestamp historical "
                             f"candles for: {pair} in {time_frame}")
        except Exception as e:
            self.logger.exception(e, True, f"Error while fetching historical candles: {e}")
        if ohlcv_data:
            await self.push(time_frame, pair, [ohlcv[-1] for ohlcv in ohlcv_data], replace_all=True)
