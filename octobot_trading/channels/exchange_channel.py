# pylint: disable=E0203
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

from octobot_channels.consumer import Consumer, InternalConsumer, SupervisedConsumer
from octobot_channels.producer import Producer
from octobot_commons.logging.logging_util import get_logger

from octobot_channels.channels.channel import Channel

from octobot_channels.constants import CHANNEL_WILDCARD
from octobot_channels.channels.channel_instances import ChannelInstances


class ExchangeChannelConsumer(Consumer):
    pass


class ExchangeSimulatorChannelConsumer(SupervisedConsumer):
    pass


class ExchangeChannelInternalConsumer(InternalConsumer):
    pass


class ExchangeChannelSupervisedConsumer(SupervisedConsumer):
    pass


class ExchangeChannelProducer(Producer):
    pass


class ExchangeChannel(Channel):
    PRODUCER_CLASS = ExchangeChannelProducer
    CONSUMER_CLASS = ExchangeChannelConsumer
    SIMULATOR_CONSUMER_CLASS = ExchangeSimulatorChannelConsumer

    CRYPTOCURRENCY_KEY = "cryptocurrency"
    SYMBOL_KEY = "symbol"

    def __init__(self, exchange_manager):
        super().__init__()
        self.logger = get_logger(f"{self.__class__.__name__}[{exchange_manager.exchange_name}]")
        self.exchange_manager = exchange_manager
        self.exchange = exchange_manager.exchange

        self.filter_send_counter = 0
        self.should_send_filter = False

    async def new_consumer(self,
                           callback: object = None,
                           consumer_instance: object = None,
                           size=0,
                           symbol=CHANNEL_WILDCARD,
                           cryptocurrency=CHANNEL_WILDCARD,
                           **kwargs):
        consumer = consumer_instance \
            if consumer_instance else (self.CONSUMER_CLASS(callback, size=size)
                                       if not self.exchange_manager.is_backtesting else
                                       self.SIMULATOR_CONSUMER_CLASS(callback, size=size))
        await self._add_new_consumer_and_run(consumer,
                                             cryptocurrency=cryptocurrency,
                                             symbol=symbol,
                                             **kwargs)
        await self._check_producers_state()
        return consumer

    async def _check_producers_state(self) -> None:  # TODO useless (bc copy of Channel.__check_producers_state)
        if not self.get_filtered_consumers() and not self.is_paused:
            self.is_paused = True
            for producer in self.get_producers():
                await producer.pause()
        elif self.get_filtered_consumers() and self.is_paused:
            self.is_paused = False
            for producer in self.get_producers():
                await producer.resume()

    def get_filtered_consumers(self,
                               cryptocurrency=CHANNEL_WILDCARD,
                               symbol=CHANNEL_WILDCARD):
        return self.get_consumer_from_filters({
            self.CRYPTOCURRENCY_KEY: cryptocurrency,
            self.SYMBOL_KEY: symbol
        })

    async def _add_new_consumer_and_run(self, consumer,
                                        cryptocurrency=CHANNEL_WILDCARD,
                                        symbol=CHANNEL_WILDCARD):
        self.add_new_consumer(consumer,
                              {
                                  self.CRYPTOCURRENCY_KEY: cryptocurrency,
                                  self.SYMBOL_KEY: symbol
                              })
        await self._run_consumer(consumer,
                                 symbol=symbol)

    async def _run_consumer(self, consumer,
                            symbol=CHANNEL_WILDCARD):
        await consumer.run()
        self.logger.debug(f"Consumer started for symbol {symbol}")


class TimeFrameExchangeChannel(ExchangeChannel):
    TIME_FRAME_KEY = "time_frame"

    def get_filtered_consumers(self,
                               cryptocurrency=CHANNEL_WILDCARD,
                               symbol=CHANNEL_WILDCARD,
                               time_frame=CHANNEL_WILDCARD):
        return self.get_consumer_from_filters({
            self.CRYPTOCURRENCY_KEY: cryptocurrency,
            self.SYMBOL_KEY: symbol,
            self.TIME_FRAME_KEY: time_frame
        })

    async def _add_new_consumer_and_run(self, consumer,
                                        cryptocurrency=CHANNEL_WILDCARD,
                                        symbol=CHANNEL_WILDCARD,
                                        time_frame=CHANNEL_WILDCARD):
        self.add_new_consumer(consumer,
                              {
                                  self.CRYPTOCURRENCY_KEY: cryptocurrency,
                                  self.SYMBOL_KEY: symbol,
                                  self.TIME_FRAME_KEY: time_frame
                              })
        await self._run_consumer(consumer,
                                 symbol=symbol)


def set_chan(chan, name) -> None:
    chan_name = chan.get_name() if name else name

    try:
        exchange_chan = ChannelInstances.instance().channels[chan.exchange_manager.id]
    except KeyError:
        ChannelInstances.instance().channels[chan.exchange_manager.id] = {}
        exchange_chan = ChannelInstances.instance().channels[chan.exchange_manager.id]

    if chan_name not in exchange_chan:
        exchange_chan[chan_name] = chan
    else:
        raise ValueError(f"Channel {chan_name} already exists.")


def get_exchange_channels(exchange_id) -> dict:
    try:
        return ChannelInstances.instance().channels[exchange_id]
    except KeyError:
        raise KeyError(f"Channels not found on exchange with id: {exchange_id}")


def del_exchange_channel_container(exchange_id):
    try:
        ChannelInstances.instance().channels.pop(exchange_id, None)
    except KeyError:
        raise KeyError(f"Channels not found on exchange with id: {exchange_id}")


def get_chan(chan_name, exchange_id) -> ExchangeChannel:
    try:
        return ChannelInstances.instance().channels[exchange_id][chan_name]
    except KeyError:
        # get_logger(ExchangeChannel.__name__).error(f"Channel {chan_name} not found on exchange with id: "
        #                                            f"{exchange_id}")
        raise KeyError(f"Channel {chan_name} not found on exchange with id: {exchange_id}")


def del_chan(chan_name, exchange_id) -> None:
    try:
        ChannelInstances.instance().channels[exchange_id].pop(chan_name, None)
    except KeyError:
        get_logger(ExchangeChannel.__name__).warning(f"Can't del chan {chan_name} on exchange with id: {exchange_id}")
