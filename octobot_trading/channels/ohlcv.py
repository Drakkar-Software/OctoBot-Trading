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
from asyncio import CancelledError, Queue

from octobot_channels import CHANNEL_WILDCARD, CONSUMER_CALLBACK_TYPE
from octobot_commons.logging.logging_util import get_logger

from octobot_trading.channels.exchange_channel import ExchangeChannel, ExchangeChannelConsumer
from octobot_channels.consumer import Consumer
from octobot_channels.producer import Producer


class OHLCVProducer(Producer):
    def __init__(self, channel):
        self.logger = get_logger(self.__class__.__name__)
        super().__init__(channel)

    async def push(self, time_frame, symbol, candle, replace_all=False, partial=False):
        await self.perform(time_frame, symbol, candle, replace_all, partial)

    async def perform(self, time_frame, symbol, candle, replace_all=False, partial=False):
        try:
            if (CHANNEL_WILDCARD in self.channel.consumers and self.channel.consumers[CHANNEL_WILDCARD]) or \
                    (symbol in self.channel.consumers or time_frame in self.channel.consumers[symbol]):
                self.channel.exchange_manager.uniformize_candles_if_necessary(candle)
                await self.channel.exchange_manager.get_symbol_data(symbol).handle_candles_update(time_frame,
                                                                                                  candle,
                                                                                                  replace_all=replace_all,
                                                                                                  partial=partial)
                if candle and (partial or replace_all):
                    candle = candle[-1]
                await self.send(time_frame, symbol, candle)
                await self.send(time_frame, symbol, candle, True)
        except CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.error(f"exception when triggering update: {e}")
            self.logger.exception(e)

    async def send(self, time_frame, symbol, candle, is_wildcard=False):
        for consumer in self.channel.get_consumers_by_timeframe(symbol=CHANNEL_WILDCARD if is_wildcard else symbol,
                                                                time_frame=time_frame):
            await consumer.queue.put({
                "exchange": self.channel.exchange_manager.exchange.name,
                "symbol": symbol,
                "time_frame": time_frame,
                "candle": candle
            })


class OHLCVChannel(ExchangeChannel):
    WITH_TIME_FRAME = True
