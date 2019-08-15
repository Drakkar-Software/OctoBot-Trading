# cython: language_level=3
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
from asyncio import Queue

from octobot_channels.consumer import Consumer
from octobot_channels.producer import Producer
from octobot_commons.logging.logging_util import get_logger

from octobot_channels.channels.channel import Channel, Channels

from octobot_channels import CONSUMER_CALLBACK_TYPE, CHANNEL_WILDCARD
from octobot_channels.channels.channel_instances import ChannelInstances


class ExchangeChannel(Channel):
    FILTER_SIZE = 1
    WITH_TIME_FRAME = False

    def __init__(self, exchange_manager):
        super().__init__()
        self.logger = get_logger(f"{self.__class__.__name__}[{exchange_manager.exchange.name}]")
        self.exchange_manager = exchange_manager
        self.exchange = exchange_manager.exchange

        self.filter_send_counter = 0
        self.should_send_filter = False

    async def new_consumer(self,
                           callback: CONSUMER_CALLBACK_TYPE,
                           size=0,
                           symbol=CHANNEL_WILDCARD,
                           filter_size=False):
        consumer = ExchangeChannelConsumer(callback, size=size, filter_size=filter_size)
        await self.__add_new_consumer_and_run(consumer, symbol=symbol, with_time_frame=self.WITH_TIME_FRAME)
        return consumer

    def will_send(self):
        self.filter_send_counter += 1

    def has_send(self):
        if self.should_send_filter:
            self.filter_send_counter = 0
            self.should_send_filter = False

    def get_consumers(self, symbol=None):
        if not self.consumers:
            return self.consumers

        if not symbol:
            symbol = CHANNEL_WILDCARD
        try:
            self.should_send_filter = self.filter_send_counter >= self.FILTER_SIZE
            return [consumer
                    for consumer in self.consumers[symbol]
                    if not consumer.filter_size or self.should_send_filter]
        except KeyError:
            Channel.init_consumer_if_necessary(self.consumers, symbol)
            return self.consumers[symbol]

    def get_consumers_by_timeframe(self, time_frame, symbol):
        if not symbol:
            symbol = CHANNEL_WILDCARD
        try:
            should_send_filter: int = self.filter_send_counter >= self.FILTER_SIZE
            if should_send_filter:
                self.filter_send_counter = 0
            return [consumer
                    for consumer in self.consumers[symbol][time_frame]
                    if not consumer.filter_size or should_send_filter]
        except KeyError:
            Channel.init_consumer_if_necessary(self.consumers, symbol, is_dict=True)
            Channel.init_consumer_if_necessary(self.consumers[symbol], time_frame)
            return self.consumers[symbol][time_frame]

    async def __add_new_consumer_and_run(self, consumer, symbol=CHANNEL_WILDCARD, with_time_frame=False):
        if symbol:
            if with_time_frame:
                # create dict and list if required
                Channel.init_consumer_if_necessary(self.consumers, symbol, is_dict=True)

                for time_frame in self.exchange_manager.time_frames:
                    Channel.init_consumer_if_necessary(self.consumers[symbol], time_frame)
                    self.consumers[symbol][time_frame].append(consumer)
            else:
                # create dict and list if required
                Channel.init_consumer_if_necessary(self.consumers, symbol)

                self.consumers[symbol].append(consumer)
        else:
            self.consumers[CHANNEL_WILDCARD] = [consumer]
        await consumer.run()
        self.logger.info(f"Consumer started for symbol {symbol}")


class ExchangeChannelConsumer(Consumer):
    async def consume(self):
        while not self.should_stop:
            try:
                await self.callback(**(await self.queue.get()))
            except Exception as e:
                self.logger.exception(f"Exception when calling callback : {e}")


class ExchangeChannelProducer(Producer):
    async def send_with_wildcard(self, **kwargs):
        await self.send(**kwargs)
        await self.send(**kwargs, is_wildcard=True)

    async def pause(self, **kwargs) -> None:
        pass

    async def resume(self, **kwargs) -> None:
        pass


class ExchangeChannels(Channels):
    @staticmethod
    def set_chan(chan, name) -> None:
        chan_name = chan.get_name() if name else name

        try:
            exchange_chan = ChannelInstances.instance().channels[chan.exchange_manager.exchange.name]
        except KeyError:
            ChannelInstances.instance().channels[chan.exchange_manager.exchange.name] = {}
            exchange_chan = ChannelInstances.instance().channels[chan.exchange_manager.exchange.name]

        if chan_name not in exchange_chan:
            exchange_chan[chan_name] = chan
        else:
            raise ValueError(f"Channel {chan_name} already exists.")

    @staticmethod
    def get_chan(chan_name: str, exchange_name: str) -> ExchangeChannel:
        try:
            return ChannelInstances.instance().channels[exchange_name][chan_name]
        except KeyError:
            get_logger(__class__.__name__).error(f"Channel {chan_name} not found on {exchange_name}")
            return None
