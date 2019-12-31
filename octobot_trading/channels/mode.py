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
from octobot_channels.channels.channel import CHANNEL_WILDCARD
from octobot_commons.constants import INIT_EVAL_NOTE

from octobot_trading.channels.exchange_channel import ExchangeChannel, ExchangeChannelProducer, \
    ExchangeChannelInternalConsumer
from octobot_trading.enums import EvaluatorStates


class ModeChannelConsumer(ExchangeChannelInternalConsumer):
    pass


class ModeChannelProducer(ExchangeChannelProducer):
    async def send(self,
                   final_note=INIT_EVAL_NOTE,
                   trading_mode_name=CHANNEL_WILDCARD,
                   cryptocurrency=CHANNEL_WILDCARD,
                   symbol=CHANNEL_WILDCARD,
                   time_frame=None,
                   state=EvaluatorStates.NEUTRAL):
        for consumer in self.channel.get_filtered_consumers(trading_mode_name=trading_mode_name,
                                                            cryptocurrency=cryptocurrency,
                                                            symbol=symbol,
                                                            time_frame=time_frame):
            await consumer.queue.put({
                "final_note": final_note,
                "state": state,
                "trading_mode_name": trading_mode_name,
                "cryptocurrency": cryptocurrency,
                "symbol": symbol,
                "time_frame": time_frame
            })


class ModeChannel(ExchangeChannel):
    PRODUCER_CLASS = ModeChannelProducer
    CONSUMER_CLASS = ModeChannelConsumer

    TRADING_MODE_NAME_KEY = "trading_mode_name"
    CRYPTOCURRENCY_KEY = "cryptocurrency"
    SYMBOL_KEY = "symbol"
    TIME_FRAME_KEY = "time_frame"

    async def new_consumer(self,
                           consumer_instance: ModeChannelConsumer,
                           size=0,
                           trading_mode_name=CHANNEL_WILDCARD,
                           cryptocurrency=CHANNEL_WILDCARD,
                           symbol=CHANNEL_WILDCARD,
                           time_frame=CHANNEL_WILDCARD,
                           filter_size=False):
        await self._add_new_consumer_and_run(consumer_instance,
                                             trading_mode_name=trading_mode_name,
                                             cryptocurrency=cryptocurrency,
                                             symbol=symbol,
                                             time_frame=time_frame)

    def get_filtered_consumers(self,
                               trading_mode_name=CHANNEL_WILDCARD,
                               cryptocurrency=CHANNEL_WILDCARD,
                               symbol=CHANNEL_WILDCARD,
                               time_frame=CHANNEL_WILDCARD):
        return self.get_consumer_from_filters({
            self.TRADING_MODE_NAME_KEY: trading_mode_name,
            self.CRYPTOCURRENCY_KEY: cryptocurrency,
            self.SYMBOL_KEY: symbol,
            self.TIME_FRAME_KEY: time_frame
        })

    async def _add_new_consumer_and_run(self, consumer,
                                        trading_mode_name=CHANNEL_WILDCARD,
                                        cryptocurrency=CHANNEL_WILDCARD,
                                        symbol=CHANNEL_WILDCARD,
                                        time_frame=None):
        consumer_filters: dict = {
            self.TRADING_MODE_NAME_KEY: trading_mode_name,
            self.CRYPTOCURRENCY_KEY: cryptocurrency,
            self.SYMBOL_KEY: symbol,
            self.TIME_FRAME_KEY: time_frame,
        }

        self.add_new_consumer(consumer, consumer_filters)
        await consumer.run()
        self.logger.debug(f"Consumer started for : "
                          f"[trading_mode_name={trading_mode_name},"
                          f" cryptocurrency={cryptocurrency},"
                          f" symbol={symbol},"
                          f" time_frame={time_frame}]")
