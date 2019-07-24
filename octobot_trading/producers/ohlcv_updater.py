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

from octobot_commons.enums import TimeFramesMinutes, PriceIndexes
from octobot_websockets.constants import MINUTE_TO_SECONDS

from octobot_trading.channels.ohlcv import OHLCVProducer


class OHLCVUpdater(OHLCVProducer):
    OHLCV_LIMIT = 5  # should be < to candle manager's MAX_CANDLES_COUNT
    OHLCV_OLD_LIMIT = 200  # should be < to candle manager's MAX_CANDLES_COUNT
    OHLCV_ON_ERROR_TIME = 5
    OHLCV_ON_FETCHED_HISTORY_TIME = 10

    def __init__(self, channel):
        super().__init__(channel)
        self.should_stop = False
        self.channel = channel
        self.tasks = []

    """
    Creates OHLCV refresh tasks
    """

    async def start(self):
        self.tasks = [
            asyncio.create_task(self._candle_callback(self.channel.exchange_manager.traded_pairs, time_frame))
            for time_frame in self.channel.exchange_manager.time_frames]

    """
    Manage timeframe OHLCV data refreshing for all pairs
    """

    async def _candle_callback(self, pairs, time_frame):
        last_candle: dict = {}
        time_frame_sleep: int = TimeFramesMinutes[time_frame] * MINUTE_TO_SECONDS

        # fetch history
        for pair in pairs:
            candles: list = await self.channel.exchange_manager.exchange \
                .get_symbol_prices(pair, time_frame, limit=self.OHLCV_OLD_LIMIT)

            await self.push(time_frame, pair, candles[:-1], replace_all=True)

        await asyncio.sleep(self.OHLCV_ON_FETCHED_HISTORY_TIME)

        while not self.should_stop:
            try:
                candles: list = []
                for pair in pairs:
                    candles: list = await self.channel.exchange_manager.exchange \
                        .get_symbol_prices(pair, time_frame, limit=self.OHLCV_LIMIT)

                    await self.push(time_frame, pair, candles[:-1], partial=True)  # push only completed candles

                if candles:
                    last_candle = candles[-1]
                    self.channel.exchange_manager.uniformize_candles_if_necessary(last_candle)
                else:
                    last_candle = {}

                if last_candle:
                    should_sleep_time = last_candle[PriceIndexes.IND_PRICE_TIME.value] + time_frame_sleep - time.time()

                    if should_sleep_time > time_frame_sleep:
                        should_sleep_time = time_frame_sleep

                    await asyncio.sleep(should_sleep_time)
                else:
                    await asyncio.sleep(time_frame_sleep)
            except Exception as e:
                self.logger.exception(f"Failed to update ohlcv data in  {time_frame} : {e}")
                await asyncio.sleep(self.OHLCV_ON_ERROR_TIME)

#     async def force_refresh_data(self, time_frame, symbol):
#         if not self.backtesting_enabled:
#             await self._refresh_time_frame_data(time_frame, symbol, self.ohlcv_producers[symbol][time_frame])
#
#     # backtesting
#     def _init_backtesting_if_necessary(self, time_frames):
#         # test if we need to initialize backtesting features
#         if self.backtesting_enabled:
#             for symbol in self.updated_traded_pairs:
#                 self.simulator.get_exchange().init_candles_offset(time_frames, symbol)
#
#     # currently used only during backtesting, will force refresh of each supervised task
#     async def update_backtesting_order_status(self):
#         order_manager = self.simulator.get_trader().get_order_manager()
#         await order_manager.force_update_order_status(simulated_time=True)
#
#     async def trigger_symbols_finalize(self):
#         sort_symbol_evaluators = sorted(self.symbol_evaluators,
#                                         key=lambda s: abs(s.get_average_strategy_eval(self.simulator)),
#                                         reverse=True)
#         for symbol_evaluator in sort_symbol_evaluators:
#             await symbol_evaluator.finalize(self.simulator)
