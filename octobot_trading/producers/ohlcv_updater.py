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
import time

from ccxt.base.errors import NotSupported

from octobot_commons.constants import MINUTE_TO_SECONDS
from octobot_commons.enums import TimeFramesMinutes, PriceIndexes
from octobot_trading.channels import OHLCV_CHANNEL
from octobot_trading.channels.ohlcv import OHLCVProducer


class OHLCVUpdater(OHLCVProducer):
    CHANNEL_NAME = OHLCV_CHANNEL
    OHLCV_LIMIT = 5  # should be < to candle manager's MAX_CANDLES_COUNT
    OHLCV_OLD_LIMIT = 200  # should be < to candle manager's MAX_CANDLES_COUNT
    OHLCV_ON_ERROR_TIME = 5
    OHLCV_MIN_REFRESH_TIME = 3

    def __init__(self, channel):
        super().__init__(channel)
        self.tasks = []
        self.is_initialized = False

    """
    Creates OHLCV refresh tasks
    """

    async def start(self):
        if not self.is_initialized:
            for time_frame in self.channel.exchange_manager.time_frames:
                for pair in self.channel.exchange_manager.traded_pairs:
                    await self.__initialize_candles(time_frame, pair)
        self.is_initialized = True

        self.tasks = [
            asyncio.create_task(self.__candle_callback(time_frame, pair))
            for time_frame in self.channel.exchange_manager.time_frames
            for pair in self.channel.exchange_manager.traded_pairs]

    """
    Manage timeframe OHLCV data refreshing for all pairs
    """

    async def __initialize_candles(self, time_frame, pair):
        # fetch history
        candles: list = await self.channel.exchange_manager.exchange \
            .get_symbol_prices(pair, time_frame, limit=self.OHLCV_OLD_LIMIT)
        await self.push(time_frame, pair, candles[:-1], replace_all=True)

    async def __candle_callback(self, time_frame, pair):
        time_frame_sleep: int = TimeFramesMinutes[time_frame] * MINUTE_TO_SECONDS
        last_candle_timestamp: float = 0

        while not self.should_stop and not self.channel.is_paused:
            try:
                candles: list = await self.channel.exchange_manager.exchange \
                    .get_symbol_prices(pair, time_frame, limit=self.OHLCV_LIMIT)

                if candles:
                    last_candle: list = candles[-1]
                    self.channel.exchange_manager.uniformize_candles_if_necessary(last_candle)
                else:
                    last_candle: list = []

                if last_candle:
                    current_candle_timestamp: float = last_candle[PriceIndexes.IND_PRICE_TIME.value]
                    should_sleep_time: float = current_candle_timestamp + time_frame_sleep - time.time()

                    if last_candle_timestamp == current_candle_timestamp:
                        should_sleep_time = self.OHLCV_MIN_REFRESH_TIME
                    else:
                        # A fresh candle happened
                        last_candle_timestamp = current_candle_timestamp
                        await self.push(time_frame, pair, candles[:-1], partial=True)  # push only completed candles

                        if should_sleep_time < self.OHLCV_MIN_REFRESH_TIME:
                            should_sleep_time = self.OHLCV_MIN_REFRESH_TIME
                        elif should_sleep_time > time_frame_sleep:
                            should_sleep_time = time_frame_sleep

                    await asyncio.sleep(should_sleep_time)
                else:
                    await asyncio.sleep(time_frame_sleep)
            except NotSupported:
                self.logger.warning(
                    f"{self.channel.exchange_manager.exchange.name} is not supporting updates")
                await self.pause()
            except Exception as e:
                self.logger.exception(f"Failed to update ohlcv data for {pair} on {time_frame} : {e}")
                await asyncio.sleep(self.OHLCV_ON_ERROR_TIME)

    # async def resume(self) -> None: TODO
    #     await super().resume()
    #     for task in self.tasks:
    #         task.cancel()
    #     await self.run()
