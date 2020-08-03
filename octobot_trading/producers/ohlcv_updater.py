# pylint: disable=E0611
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
from octobot_trading.constants import OHLCV_CHANNEL
from octobot_trading.channels.ohlcv import OHLCVProducer


class OHLCVUpdater(OHLCVProducer):
    CHANNEL_NAME = OHLCV_CHANNEL
    OHLCV_LIMIT = 5  # should be < to candle manager's MAX_CANDLES_COUNT
    OHLCV_OLD_LIMIT = 200  # should be < to candle manager's MAX_CANDLES_COUNT
    OHLCV_ON_ERROR_TIME = 5
    OHLCV_MIN_REFRESH_TIME = 1
    OHLCV_REFRESH_TIME_THRESHOLD = 1.5  # to prevent spamming at candle closing

    OHLCV_INITIALIZATION_TIMEOUT = 60
    OHLCV_INITIALIZATION_RETRY_DELAY = 10

    def __init__(self, channel):
        super().__init__(channel)
        self.tasks = []
        self.is_initialized = False
        self.initialized_candles_by_tf_by_symbol = {}

    async def start(self):
        """
        Creates OHLCV refresh tasks
        """
        if not self.is_initialized:
            await self._initialize()
        if self.channel is not None:
            if self.channel.is_paused:
                await self.pause()
            else:
                self.tasks = [
                    asyncio.create_task(self._candle_callback(time_frame, pair))
                    for time_frame in self.channel.exchange_manager.exchange_config.traded_time_frames
                    for pair in self.channel.exchange_manager.exchange_config.traded_symbol_pairs]

    def _get_traded_pairs(self):
        return self.channel.exchange_manager.exchange_config.traded_symbol_pairs

    def _get_time_frames(self):
        return self.channel.exchange_manager.exchange_config.traded_time_frames

    async def _initialize(self):
        try:
            await asyncio.gather(*[
                self._initialize_candles(time_frame, pair, True)
                for time_frame in self._get_time_frames()
                for pair in self._get_traded_pairs()
            ])
        except Exception as e:
            self.logger.exception(e, True, f"Error while initializing candles: {e}")
        finally:
            self.logger.debug("Candle history initial fetch completed")
            self.is_initialized = True

    async def _initialize_candles(self, time_frame, pair, should_retry):
        """
        Manage timeframe OHLCV data refreshing for all pairs
        """
        self._set_initialized(pair, time_frame, False)
        # fetch history
        candles: list = await self.channel.exchange_manager.exchange \
            .get_symbol_prices(pair, time_frame, limit=self.OHLCV_OLD_LIMIT)
        self.channel.exchange_manager.uniformize_candles_if_necessary(candles)
        if candles and len(candles) > 1:
            self._set_initialized(pair, time_frame, True)
            await self.channel.exchange_manager.get_symbol_data(pair) \
                .handle_candles_update(time_frame, candles[:-1], replace_all=True, partial=False)
            self.logger.debug(f"Candle history loaded for {pair} on {time_frame}")
        elif should_retry:
            # When candle history cannot be loaded, retry to load it later
            self.logger.warning(f"Failed to initialize candle history for {pair} on {time_frame}. Retrying in "
                                f"{self.OHLCV_INITIALIZATION_RETRY_DELAY} seconds")
            # retry only once
            await asyncio.sleep(self.OHLCV_INITIALIZATION_RETRY_DELAY)
            await self._initialize_candles(time_frame, pair, False)
        else:
            self.logger.warning(f"Failed to initialize candle history for {pair} on {time_frame}. Retrying on "
                                f"the next time frame update")

    async def _ensure_candles_initialization(self, pair):
        init_coroutines = tuple(
            self._initialize_candles(time_frame, pair, False)
            for time_frame, initialized in self.initialized_candles_by_tf_by_symbol[pair].items()
            if not initialized
        )
        # call gather only if init_coroutines is not empty for optimization purposes
        if init_coroutines:
            await asyncio.gather(*init_coroutines)

    async def _candle_callback(self, time_frame, pair):
        time_frame_sleep: int = TimeFramesMinutes[time_frame] * MINUTE_TO_SECONDS
        last_candle_timestamp: float = 0

        while not self.should_stop and not self.channel.is_paused:
            try:
                start_update_time = time.time()
                await self._ensure_candles_initialization(pair)
                # skip uninitialized candles
                if self.initialized_candles_by_tf_by_symbol[pair][time_frame]:
                    candles: list = await self.channel.exchange_manager.exchange.get_symbol_prices(
                        pair,
                        time_frame,
                        limit=self.OHLCV_LIMIT)
                    if candles:
                        last_candle: list = candles[-1]
                        self.channel.exchange_manager.uniformize_candles_if_necessary(candles)
                    else:
                        last_candle: list = []

                    if last_candle:
                        current_candle_timestamp: float = last_candle[PriceIndexes.IND_PRICE_TIME.value]
                        should_sleep_time: float = current_candle_timestamp + time_frame_sleep - time.time()

                        # if we're trying to refresh the current candle => useless
                        if last_candle_timestamp == current_candle_timestamp:
                            should_sleep_time = self._ensure_correct_sleep_time(
                                should_sleep_time + time_frame_sleep + self.OHLCV_REFRESH_TIME_THRESHOLD,
                                time_frame_sleep)
                        else:
                            # A fresh candle happened
                            last_candle_timestamp = current_candle_timestamp
                            await self.push(time_frame, pair, candles[:-1], partial=True)  # push only completed candles

                        await asyncio.sleep(self._ensure_correct_sleep_time(should_sleep_time, time_frame_sleep))
                    else:
                        # TODO think about asyncio.call_at or call_later
                        await asyncio.sleep(time_frame_sleep)
                else:
                    # candles on this time frame have not been initialized: sleep until the next candle update
                    await asyncio.sleep(max(0.0, time_frame_sleep - (time.time() - start_update_time)))
            except NotSupported:
                self.logger.warning(
                    f"{self.channel.exchange_manager.exchange_name} is not supporting updates")
                await self.pause()
            except Exception as e:
                self.logger.exception(e, True, f"Failed to update ohlcv data for {pair} on {time_frame} : {e}")
                await asyncio.sleep(self.OHLCV_ON_ERROR_TIME)

    def _ensure_correct_sleep_time(self, sleep_time_candidate, time_frame_sleep):
        if sleep_time_candidate < OHLCVUpdater.OHLCV_MIN_REFRESH_TIME:
            return OHLCVUpdater.OHLCV_MIN_REFRESH_TIME
        elif sleep_time_candidate > time_frame_sleep:
            return time_frame_sleep
        return sleep_time_candidate

    def _set_initialized(self, pair, time_frame, initialized):
        if pair not in self.initialized_candles_by_tf_by_symbol:
            self.initialized_candles_by_tf_by_symbol[pair] = {}
        self.initialized_candles_by_tf_by_symbol[pair][time_frame] = initialized

    async def resume(self) -> None:
        await super().resume()
        if not self.is_running:
            for task in self.tasks:
                task.cancel()
            await self.run()

    # async def config_callback(self, exchange, cryptocurrency, symbols, time_frames):
    #     if symbols:
    #         for pair in symbols:
    #             self.__create_pair_candle_task(pair)
    #             self.logger.info(f"global_data_callback: added {pair}")
    #
    #     if time_frames:
    #         for time_frame in time_frames:
    #             self.__create_time_frame_candle_task(time_frame)
    #             self.logger.info(f"global_data_callback: added {time_frame}")
