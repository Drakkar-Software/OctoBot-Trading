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

import octobot_commons.constants as common_constants
import octobot_commons.enums as common_enums

import octobot_trading.errors as errors
import octobot_trading.constants as constants
import octobot_trading.exchange_data.ohlcv.channel.ohlcv as ohlcv_channel
import octobot_trading.exchanges as exchanges


class OHLCVUpdater(ohlcv_channel.OHLCVProducer):
    CHANNEL_NAME = constants.OHLCV_CHANNEL
    OHLCV_LIMIT = 5  # should be < to candle manager's MAX_CANDLES_COUNT
    OHLCV_OLD_LIMIT = constants.DEFAULT_CANDLE_HISTORY_SIZE  # should be <= to candle manager's MAX_CANDLES_COUNT
    OHLCV_ON_ERROR_TIME = 5
    OHLCV_MIN_REFRESH_TIME = 1
    OHLCV_REFRESH_TIME_THRESHOLD = 1.5  # to prevent spamming at candle closing
    OHLCV_MISSING_DATA_REFRESH_RETRY_MAX_DELAY = 30 * common_constants.MINUTE_TO_SECONDS

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
            await self._initialize(False)
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

    async def fetch_and_push(self):
        return await self._initialize(True)

    async def _initialize(self, push_initialization_candles):
        try:
            initial_candles_data = await asyncio.gather(*[
                self._initialize_candles(time_frame, pair, True)
                for time_frame in self._get_time_frames()
                for pair in self._get_traded_pairs()
            ])
            if push_initialization_candles:
                await self._push_initial_candles(initial_candles_data)
        except Exception as e:
            self.logger.exception(e, True, f"Error while initializing candles: {e}")
        finally:
            self.logger.debug("Candle history initial fetch completed")
            self.is_initialized = True

    def _get_historical_candles_count(self):
        if self.channel.exchange_manager.exchange_config.required_historical_candles_count > 0:
            if self.channel.exchange_manager.exchange_name in constants.FULL_CANDLE_HISTORY_EXCHANGES:
                return self.channel.exchange_manager.exchange_config.required_historical_candles_count
            else:
                self.logger.warning(f"Can't initialize the required "
                                    f"{self.channel.exchange_manager.exchange_config.required_historical_candles_count}"
                                    f" historical candles: {self.channel.exchange_manager.exchange_name} is not "
                                    f"supporting candles history.")
        return self.OHLCV_OLD_LIMIT

    async def _get_init_candles(self, time_frame, pair):
        historical_candles_count_limit = self._get_historical_candles_count()
        if historical_candles_count_limit > constants.DEFAULT_CANDLE_HISTORY_SIZE:
            tf_seconds = common_enums.TimeFramesMinutes[time_frame] * common_constants.MINUTE_TO_SECONDS
            end_time = time.time() * common_constants.MSECONDS_TO_SECONDS
            # add 1 to historical_candles_count_limit to fetch the required count (otherwise one is missing)
            start_time = end_time - (historical_candles_count_limit + 1) * tf_seconds * \
                common_constants.MSECONDS_TO_SECONDS
            candles = []
            async for new_candles in exchanges.get_historical_ohlcv(self.channel.exchange_manager, pair,
                                                                    time_frame, start_time, end_time):
                candles += new_candles
            return candles
        candles: list = await self.channel.exchange_manager.exchange \
            .get_symbol_prices(pair, time_frame, limit=self.OHLCV_OLD_LIMIT)
        self.channel.exchange_manager.exchange.uniformize_candles_if_necessary(candles)
        return candles

    async def _initialize_candles(self, time_frame, pair, should_retry) -> (str, common_enums.TimeFrames, list):
        """
        Manage timeframe OHLCV data refreshing for all pairs
        :return: a tuple with (trading pair, time_frame, fetched candles)
        """
        self._set_initialized(pair, time_frame, False)
        # fetch history
        candles = None
        try:
            candles: list = await self._get_init_candles(time_frame, pair)
        except errors.FailedRequest as e:
            self.logger.warning(str(e))
        if candles and len(candles) > 1:
            self._set_initialized(pair, time_frame, True)
            await self.channel.exchange_manager.get_symbol_data(pair) \
                .handle_candles_update(time_frame, candles[:-1], replace_all=True, partial=False)
            self.logger.debug(f"Candle history loaded for {pair} on {time_frame}")
            return pair, time_frame, candles
        elif should_retry:
            # When candle history cannot be loaded, retry to load it later
            self.logger.warning(f"Failed to initialize candle history for {pair} on {time_frame}. Retrying in "
                                f"{self.OHLCV_INITIALIZATION_RETRY_DELAY} seconds")
            # retry only once
            await asyncio.sleep(self.OHLCV_INITIALIZATION_RETRY_DELAY)
            return await self._initialize_candles(time_frame, pair, False)
        else:
            self.logger.warning(f"Failed to initialize candle history for {pair} on {time_frame}. Retrying on "
                                f"the next time frame update")
            return None

    async def _push_initial_candles(self, initial_candles_data):
        self.logger.debug("Pushing completed initialization candles")
        for initial_candles_tuple in initial_candles_data:
            if initial_candles_tuple is not None:
                pair, time_frame, candles = initial_candles_tuple
                await self._push_complete_candles(time_frame, pair, candles)

    async def _push_complete_candles(self, time_frame, pair, candles):
        await self.push(time_frame, pair, candles[:-1], partial=True)  # push only completed candles

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
        time_frame_seconds: int = common_enums.TimeFramesMinutes[time_frame] * common_constants.MINUTE_TO_SECONDS
        time_frame_sleep: int = time_frame_seconds
        last_candle_timestamp: float = 0
        missing_data_sleep_time = min(int(time_frame_seconds / 6), self.OHLCV_MISSING_DATA_REFRESH_RETRY_MAX_DELAY)

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
                        self.channel.exchange_manager.exchange.uniformize_candles_if_necessary(candles)
                    else:
                        last_candle: list = []

                    if last_candle and len(candles) > 1:
                        last_candle_timestamp, sleep_time = await self._refresh_current_candle(
                            time_frame, pair, candles, last_candle, last_candle_timestamp, time_frame_sleep
                        )
                        await asyncio.sleep(self._ensure_correct_sleep_time(sleep_time, time_frame_sleep))
                    else:
                        # not enough candles: retry soon
                        self.logger.debug(f"Missing candles in request results for {pair} on {time_frame}, refreshing "
                                          f"in {missing_data_sleep_time} seconds (available candles: {candles}).")
                        await asyncio.sleep(missing_data_sleep_time)
                else:
                    # candles on this time frame have not been initialized: sleep until the next candle update
                    await asyncio.sleep(max(0.0, time_frame_sleep - (time.time() - start_update_time)))
            except errors.FailedRequest as e:
                self.logger.warning(str(e))
            except errors.NotSupported:
                self.logger.warning(
                    f"{self.channel.exchange_manager.exchange_name} is not supporting updates")
                await self.pause()
            except Exception as e:
                self.logger.exception(e, True, f"Failed to update ohlcv data for {pair} on {time_frame} : {e}")
                await asyncio.sleep(self.OHLCV_ON_ERROR_TIME)

    async def _refresh_current_candle(self, time_frame, pair, candles, last_candle,
                                      last_candle_timestamp, time_frame_sleep):
        current_candle_timestamp: float = last_candle[common_enums.PriceIndexes.IND_PRICE_TIME.value]
        should_sleep_time: float = current_candle_timestamp + time_frame_sleep - time.time()

        # if we're trying to refresh the current candle => useless
        if last_candle_timestamp == current_candle_timestamp:
            if should_sleep_time < 0:
                # up to date candle is not yet available on exchange: retry in a few seconds
                should_sleep_time = self._ensure_correct_sleep_time(
                    self.OHLCV_REFRESH_TIME_THRESHOLD,
                    time_frame_sleep
                )
            else:
                should_sleep_time = self._ensure_correct_sleep_time(
                    should_sleep_time + time_frame_sleep + self.OHLCV_REFRESH_TIME_THRESHOLD,
                    time_frame_sleep
                )
        else:
            # A fresh candle happened
            last_candle_timestamp = current_candle_timestamp
            await self._push_complete_candles(time_frame, pair, candles)
        return last_candle_timestamp, should_sleep_time

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
