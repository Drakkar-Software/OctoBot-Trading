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

from octobot_commons.logging.logging_util import get_logger

from octobot_trading.channels.kline import KlineProducer


class KlineUpdater(KlineProducer):
    KLINE_REFRESH_TIME = 8
    KLINE_LIMIT = 1

    def __init__(self, channel):
        super().__init__(channel)
        self.tasks = []

    """
    Creates OHLCV refresh tasks
    """

    async def start(self):
        self.tasks = [
            asyncio.create_task(self.time_frame_watcher(self.channel.exchange_manager.traded_pairs, time_frame))
            for time_frame in self.channel.exchange_manager.time_frames]

    """
    Manage timeframe OHLCV data refreshing for all pairs
    """

    async def time_frame_watcher(self, pairs, time_frame):
        while not self.should_stop:
            try:
                candle: list = []
                started_time = time.time()
                for pair in pairs:
                    candle = await self.channel.exchange_manager.exchange.get_symbol_prices(pair,
                                                                                            time_frame,
                                                                                            limit=self.KLINE_LIMIT)
                    candle = candle[0]
                    await self.push(time_frame, pair, candle)

                if candle:
                    await asyncio.sleep(self.KLINE_REFRESH_TIME - (time.time() - started_time))
            except Exception as e:
                self.logger.error(f"Failed to update kline data in {time_frame} : {e}")
