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
from asyncio import CancelledError

from octobot_channels.constants import CHANNEL_WILDCARD

from octobot_trading.channels.exchange_channel import ExchangeChannel, ExchangeChannelProducer, ExchangeChannelConsumer


class OHLCVProducer(ExchangeChannelProducer):
    async def push(self, time_frame, symbol, candle, replace_all=False, partial=False):
        await self.perform(time_frame, symbol, candle, replace_all, partial)

    async def perform(self, time_frame, symbol, candle, replace_all=False, partial=False):
        try:
            if self.channel.get_filtered_consumers(symbol=CHANNEL_WILDCARD) or \
                    self.channel.get_filtered_consumers(symbol=symbol, time_frame=time_frame):
                self.channel.exchange_manager.uniformize_candles_if_necessary(candle)
                await self.channel.exchange_manager.get_symbol_data(symbol).handle_candles_update(time_frame,
                                                                                                  candle,
                                                                                                  replace_all=replace_all,
                                                                                                  partial=partial)
                if candle and (partial or replace_all):
                    candle = candle[-1]
                await self.send(time_frame=time_frame.value, symbol=symbol, candle=candle)
        except CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.error(f"exception when triggering update: {e}")
            self.logger.exception(e)

    async def send(self, time_frame, symbol, candle):
        for consumer in self.channel.get_filtered_consumers(symbol=symbol, time_frame=time_frame):
            await consumer.queue.put({
                "exchange": self.channel.exchange_manager.exchange.name,
                "exchange_id": self.channel.exchange_manager.id,
                "symbol": symbol,
                "time_frame": time_frame,
                "candle": candle
            })


class OHLCVChannel(ExchangeChannel):
    WITH_TIME_FRAME = True
    PRODUCER_CLASS = OHLCVProducer
    CONSUMER_CLASS = ExchangeChannelConsumer
