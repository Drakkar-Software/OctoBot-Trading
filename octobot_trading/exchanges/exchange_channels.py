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
from octobot_channels.util.channel_creator import create_all_subclasses_channel

from octobot_trading.channels.exchange_channel import set_chan, get_chan, \
    ExchangeChannel, TimeFrameExchangeChannel, get_exchange_channels, del_chan, del_exchange_channel_container
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
    if exchange_manager.exchange.is_authenticated \
            and exchange_manager.trader and exchange_manager.is_trading \
            and not (
            exchange_manager.is_simulated or exchange_manager.is_backtesting or exchange_manager.is_collecting):
        await _create_authenticated_producers(exchange_manager)

    # Real data producers
    if not exchange_manager.is_backtesting:
        for updater in get_unauthenticated_updater_producers():
            if not is_exchange_managed_by_websocket(exchange_manager, updater.CHANNEL_NAME):
                await updater(get_chan(updater.CHANNEL_NAME, exchange_manager.id)).run()

    # Simulated producers
    if (
            not exchange_manager.exchange.is_authenticated
            or exchange_manager.is_simulated
            or exchange_manager.is_backtesting) \
            and exchange_manager.trader and exchange_manager.is_trading \
            and not exchange_manager.is_collecting:
        for updater in get_authenticated_updater_simulator_producers():
            await updater(get_chan(updater.CHANNEL_NAME, exchange_manager.id)).run()


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


async def stop_exchange_channels(exchange_manager, should_warn=True) -> None:
    """
    Stop exchange channels and producers
    :param exchange_manager: the related exchange manager
    :param should_warn: if an error message should be logged if an error happened during stopping process
    """
    try:
        for channel_name in list(get_exchange_channels(exchange_manager.id)):
            channel = get_chan(channel_name, exchange_manager.id)
            await channel.stop()
            for consumer in channel.consumers:
                await channel.remove_consumer(consumer)
            get_chan(channel_name, exchange_manager.id).flush()
            del_chan(channel_name, exchange_manager.id)
        del_exchange_channel_container(exchange_manager.id)
    except KeyError:
        if should_warn:
            exchange_manager.logger.error(f"No exchange channel for this exchange (id: {exchange_manager.id})")
