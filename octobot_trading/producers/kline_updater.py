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

from octobot_trading.constants import KLINE_CHANNEL
from octobot_trading.channels.kline import KlineProducer


class KlineUpdater(KlineProducer):
    CHANNEL_NAME = KLINE_CHANNEL
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
            asyncio.create_task(self.time_frame_watcher(time_frame))
            for time_frame in self.channel.exchange_manager.exchange_config.traded_time_frames]

    def __create_time_frame_kline_task(self, time_frame):
        self.tasks += asyncio.create_task(self.time_frame_watcher(time_frame))

    """
    Manage timeframe OHLCV data refreshing for all pairs
    """

    async def time_frame_watcher(self, time_frame):
        while not self.should_stop and not self.channel.is_paused:
            try:
                candle: list = []
                started_time = time.time()
                for pair in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
                    candle = await self.channel.exchange_manager.exchange.get_symbol_prices(pair,
                                                                                            time_frame,
                                                                                            limit=self.KLINE_LIMIT)
                    try:
                        candle = candle[0]
                        await self.push(time_frame, pair, candle)
                    except TypeError:
                        pass

                if candle:
                    await asyncio.sleep(self.KLINE_REFRESH_TIME - (time.time() - started_time))
            except NotSupported:
                self.logger.warning(f"{self.channel.exchange_manager.exchange_name} is not supporting updates")
                await self.pause()
            except Exception as e:
                self.logger.error(f"Failed to update kline data in {time_frame} : {e}")

    # async def config_callback(self, exchange, cryptocurrency, symbols, time_frames):
    #     if time_frames:
    #         for time_frame in time_frames:
    #             self.__create_time_frame_kline_task(time_frame)
    #             self.logger.info(f"global_data_callback: added {time_frame}")

    async def resume(self) -> None:
        await super().resume()
        if not self.is_running and self.tasks:
            for task in self.tasks:
                task.cancel()
            await self.run()
