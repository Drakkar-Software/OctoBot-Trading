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
from octobot_channels.producer import Producer
from octobot_channels.util.channel_creator import create_all_subclasses_channel
from octobot_commons.tentacles_management.class_inspector import default_parent_inspection

from octobot_trading.channels.exchange_channel import set_chan, get_chan, \
    ExchangeChannel, TimeFrameExchangeChannel
from octobot_trading.exchanges.exchange_websocket_factory import is_exchange_managed_by_websocket, \
    is_websocket_feed_requiring_init
from octobot_trading.producers import get_unauthenticated_updater_producers, get_authenticated_updater_producers
from octobot_trading.producers.simulator import get_authenticated_updater_simulator_producers


async def create_exchange_channels(exchange_manager) -> None:
    """
    Create exchange related channels
    # TODO filter creation --> not required if pause is managed
    :param exchange_manager: the related exchange manager
    """
    for exchange_channel_class_type in [ExchangeChannel, TimeFrameExchangeChannel]:
        await create_all_subclasses_channel(exchange_channel_class_type, set_chan,
                                            is_synchronized=exchange_manager.is_backtesting,
                                            exchange_manager=exchange_manager)


async def create_exchange_producers(exchange_manager) -> None:
    """
    Create exchange channels producers according to exchange manager context (backtesting, simulator, real)
    :param exchange_manager: the related exchange manager
    """

    # Always init exchange user data first on real trading
    if _should_create_authenticated_producers(exchange_manager):
        await _create_authenticated_producers(exchange_manager)

    # Real data producers
    if _should_create_unauthenticated_producers(exchange_manager):
        for updater in get_unauthenticated_updater_producers():
            if not is_exchange_managed_by_websocket(exchange_manager, updater.CHANNEL_NAME):
                await updater(get_chan(updater.CHANNEL_NAME, exchange_manager.id)).run()

    # Simulated producers
    if _should_create_simulated_producers(exchange_manager):
        for updater in get_authenticated_updater_simulator_producers():
            await updater(get_chan(updater.CHANNEL_NAME, exchange_manager.id)).run()


def _should_create_authenticated_producers(exchange_manager):
    """
    :param exchange_manager: the related exchange manager
    :return: True if should create authenticated producers
    """
    return exchange_manager.exchange.is_authenticated \
           and exchange_manager.trader and exchange_manager.is_trading \
           and not (exchange_manager.is_simulated or exchange_manager.is_backtesting or exchange_manager.is_collecting)


def _should_create_simulated_producers(exchange_manager):
    """
    :param exchange_manager: the related exchange manager
    :return: True if should create simulated producers
    """
    return (not exchange_manager.exchange.is_authenticated
            or exchange_manager.is_simulated
            or exchange_manager.is_backtesting) \
           and exchange_manager.trader and exchange_manager.is_trading and not exchange_manager.is_collecting


def _should_create_unauthenticated_producers(exchange_manager):
    """
    :param exchange_manager: the related exchange manager
    :return: True if should create unauthenticated real data producers
    """
    return not exchange_manager.is_backtesting


async def _create_authenticated_producers(exchange_manager) -> None:
    """
    Create real authenticated producers
    :param exchange_manager: the related exchange manager
    """
    for updater in get_authenticated_updater_producers():
        if is_exchange_managed_by_websocket(exchange_manager, updater.CHANNEL_NAME):
            # websocket is handling this channel: initialize data if required
            if is_websocket_feed_requiring_init(exchange_manager, updater.CHANNEL_NAME):
                try:
                    updater(get_chan(updater.CHANNEL_NAME, exchange_manager.id)).trigger_single_update()
                except Exception as e:
                    exchange_manager.logger.exception(e, True,
                                                      f"Error when initializing data for {updater.CHANNEL_NAME} "
                                                      f"channel required by websocket: {e}")
        else:
            # no websocket for this channel: start an updater
            await updater(get_chan(updater.CHANNEL_NAME, exchange_manager.id)).run()


async def _create_authenticated_producer(exchange_manager, producer) -> Producer:
    """
    Create real authenticated producers
    :param exchange_manager: the related exchange manager
    :param producer: the producer to create
    :return: the producer instance created
    """
    producer_instance = producer(get_chan(producer.CHANNEL_NAME, exchange_manager.id))
    if is_exchange_managed_by_websocket(exchange_manager, producer.CHANNEL_NAME):
        # websocket is handling this channel: initialize data if required
        if is_websocket_feed_requiring_init(exchange_manager, producer.CHANNEL_NAME):
            try:
                producer_instance.trigger_single_update()
            except Exception as e:
                exchange_manager.logger.exception(e, True,
                                                  f"Error when initializing data for {producer.CHANNEL_NAME} "
                                                  f"channel required by websocket: {e}")
    else:
        # no websocket for this channel: start an producer
        await producer_instance.run()
    return producer_instance


async def create_authenticated_producer_from_parent(exchange_manager,
                                                    parent_producer_class,
                                                    force_register_producer=False):
    """
    Create an authenticated producer from its parent class
    :param exchange_manager: the related exchange manager
    :param parent_producer_class: the authenticated producer parent class
    :param force_register_producer: force the producer to register to its channel
    """
    producer = _get_authenticated_producer_from_parent(parent_producer_class)
    if producer is not None:
        producer_instance = await _create_authenticated_producer(exchange_manager, producer)
        if force_register_producer:
            await producer_instance.channel.register_producer(producer_instance)


def _get_authenticated_producer_from_parent(parent_producer_class):
    """
    :param parent_producer_class: the authenticated producer parent class
    :return: the authenticated producer that inherit from parent_producer_class
    """
    for authenticated_producer_candidate in get_authenticated_updater_producers():
        if default_parent_inspection(authenticated_producer_candidate, parent_producer_class):
            return authenticated_producer_candidate
    return None


def requires_refresh_trigger(exchange_manager, channel):
    """
    Return True if the given channel is to be updated artificially (ex: via channel updater). In this case it
    is necessary to trigger a manual update to get the exact picture at a given time (last updater push might
    have been a few seconds ago)
    Return False if this channels updates by its exchange_manager
    and manual refresh trigger is not necessary (ex: websocket feed)
    :param exchange_manager: the related exchange manager
    :param channel: name of the channel
    :return: True if it should be refreshed via a manual trigger to be exactly up to date
    """
    return not is_exchange_managed_by_websocket(exchange_manager, channel)
