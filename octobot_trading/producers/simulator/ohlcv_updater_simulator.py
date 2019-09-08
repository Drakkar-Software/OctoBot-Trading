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
from octobot_commons.enums import TimeFrames, PriceIndexes

from octobot_trading.channels import TIME_CHANNEL, get_chan
from octobot_trading.producers.ohlcv_updater import OHLCVUpdater


class OHLCVUpdaterSimulator(OHLCVUpdater):
    async def start(self):
        await get_chan(TIME_CHANNEL, self.channel.exchange.name).new_consumer(self.handle_timestamp)

    async def handle_timestamp(self, exchange: str, timestamp: int):
        await self.push(TimeFrames.ONE_HOUR, "BTC/USDT", [[timestamp, 1, 1, 1, 1, 1]], partial=True)

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
