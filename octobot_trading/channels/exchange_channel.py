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
from asyncio import create_task

from octobot_channels.channels.channel import Channel
from octobot_channels.channels.channel_instances import ChannelInstances
from octobot_channels.constants import CHANNEL_WILDCARD
from octobot_channels.consumer import Consumer, InternalConsumer, SupervisedConsumer
from octobot_channels.producer import Producer
from octobot_commons.enums import ChannelConsumerPriorityLevels
from octobot_commons.logging.logging_util import get_logger


class ExchangeChannelConsumer(Consumer):
    """
    Consumer adapted for ExchangeChannel
    """


class ExchangeChannelInternalConsumer(InternalConsumer):
    """
    InternalConsumer adapted for ExchangeChannel
    """


class ExchangeChannelSupervisedConsumer(SupervisedConsumer):
    """
    SupervisedConsumer adapted for ExchangeChannel
    """


class ExchangeChannelProducer(Producer):
    """
    Producer adapted for ExchangeChannel
    """
    def __init__(self, channel):
        super().__init__(channel)
        self.logger = get_logger(f"{self.__class__.__name__}[{channel.exchange_manager.exchange_name}]")

    async def fetch_and_push(self):
        self.logger.error("self.fetch_and_push() is not implemented")

    def trigger_single_update(self):
        create_task(self.fetch_and_push())


class ExchangeChannel(Channel):
    PRODUCER_CLASS = ExchangeChannelProducer
    CONSUMER_CLASS = ExchangeChannelConsumer
    CRYPTOCURRENCY_KEY = "cryptocurrency"
    SYMBOL_KEY = "symbol"
    DEFAULT_PRIORITY_LEVEL = ChannelConsumerPriorityLevels.HIGH.value

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
                           size: int = 0,
                           priority_level: int = DEFAULT_PRIORITY_LEVEL,
                           symbol: str = CHANNEL_WILDCARD,
                           cryptocurrency: str = CHANNEL_WILDCARD,
                           **kwargs) -> ExchangeChannelConsumer:
        consumer = consumer_instance if consumer_instance else self.CONSUMER_CLASS(callback,
                                                                                   size=size,
                                                                                   priority_level=priority_level)
        await self._add_new_consumer_and_run(consumer,
                                             cryptocurrency=cryptocurrency,
                                             symbol=symbol,
                                             **kwargs)
        await self._check_producers_state()
        return consumer

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
        await consumer.run(with_task=not self.is_synchronized)
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
