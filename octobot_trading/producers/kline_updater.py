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

from octobot_trading.channels import OHLCV_CHANNEL, RECENT_TRADES_CHANNEL
from octobot_trading.channels.exchange_channel import ExchangeChannels
from octobot_trading.channels.kline import KlineProducer


class KlineUpdater(KlineProducer):
    def __init__(self, channel):
        super().__init__(channel)
        self.should_stop = False
        self.channel = channel

    """
    Creates OHLCV & Recent trade consumers
    """

    async def start(self):
        ExchangeChannels.get_chan(RECENT_TRADES_CHANNEL, self.channel.exchange_manager.exchange.name)\
            .new_consumer(self.recent_trades_callback)
        ExchangeChannels.get_chan(OHLCV_CHANNEL, self.channel.exchange_manager.exchange.name)\
            .new_consumer(self.ohlcv_callback)

    async def recent_trades_callback(self, symbol, recent_trades):
        try:
            for time_frame in self.channel.exchange_manager.time_frames:
                await self.push(time_frame, symbol, {}, reset=True)
        except Exception as e:
            self.logger.error(f"Failed to handle recent trade update ({e})")

    async def ohlcv_callback(self, symbol, time_frame, candle):
        try:
            await self.push(time_frame, symbol, candle, reset=True)
        except Exception as e:
            self.logger.error(f"Failed to handle ohlcv update ({e})")
