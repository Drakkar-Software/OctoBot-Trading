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

from octobot_trading.errors import AuthenticationError
from octobot_trading.exchanges.exchange_channels import create_exchange_producers, create_exchange_channels
from octobot_trading.exchanges.implementations.exchange_simulator import ExchangeSimulator
from octobot_trading.exchanges.exchange_util import get_margin_exchange_class, get_rest_exchange_class, \
    get_future_exchange_class, get_spot_exchange_class
from octobot_trading.exchanges.exchange_websocket_factory import search_and_create_websocket
from octobot_trading.exchanges.implementations.ccxt_exchange import CCXTExchange
from octobot_trading.exchanges.websockets.websockets_util import check_web_socket_config


async def create_exchanges(exchange_manager):
    if exchange_manager.is_sandboxed:
        exchange_manager.logger.info(f"Using sandbox exchange for {exchange_manager.exchange_name}")
    exchange_manager.exchange_type = CCXTExchange.create_exchange_type(exchange_manager.exchange_class_string)

    if not exchange_manager.is_backtesting:
        # real : create a rest or websocket exchange instance
        await create_real_exchange(exchange_manager)
        exchange_manager.load_constants()
        await initialize_real_exchange(exchange_manager)
    else:
        # simulated : create exchange simulator instance
        await create_simulated_exchange(exchange_manager)

    if not exchange_manager.exchange_only:
        # create exchange producers if necessary
        await create_exchange_producers(exchange_manager)

    if exchange_manager.is_backtesting:
        await init_simulated_exchange(exchange_manager)

    exchange_manager.exchange_name = exchange_manager.exchange.name
    exchange_manager.is_ready = True


async def create_real_exchange(exchange_manager) -> None:
    """
    Create and initialize real REST exchange
    :param exchange_manager: the related exchange manager
    """
    await _create_rest_exchange(exchange_manager)

    try:
        await exchange_manager.exchange.initialize()
    except AuthenticationError:
        exchange_manager.logger.error("Authentication error, retrying without authentication...")
        exchange_manager.without_auth = True
        await create_real_exchange(exchange_manager)
        return


async def initialize_real_exchange(exchange_manager):
    if not exchange_manager.exchange_only:
        await create_exchange_channels(exchange_manager)

    # create Websocket exchange if possible
    if not exchange_manager.rest_only:
        # search for websocket
        if check_web_socket_config(exchange_manager.config, exchange_manager.exchange.name):
            await search_and_create_websocket(exchange_manager)


async def _create_rest_exchange(exchange_manager) -> None:
    """
    create REST based on ccxt exchange
    :param exchange_manager: the related exchange manager
    """
    if exchange_manager.is_spot_only:
        await _search_and_create_spot_exchange(exchange_manager)
    elif exchange_manager.is_future:
        await _search_and_create_future_exchange(exchange_manager)
    elif exchange_manager.is_margin:
        await _search_and_create_margin_exchange(exchange_manager)

    if not exchange_manager.exchange:
        await _search_and_create_rest_exchange(exchange_manager)


async def create_simulated_exchange(exchange_manager):
    exchange_manager.exchange = ExchangeSimulator(exchange_manager.config, exchange_manager.exchange_type,
                                                  exchange_manager, exchange_manager.backtesting)
    await exchange_manager.exchange.initialize()
    _initialize_simulator_time_frames(exchange_manager)
    exchange_manager.exchange_config.set_config_time_frame()
    exchange_manager.exchange_config.set_config_traded_pairs()
    await create_exchange_channels(exchange_manager)


async def init_simulated_exchange(exchange_manager):
    await exchange_manager.exchange.create_backtesting_exchange_producers()


async def _search_and_create_rest_exchange(exchange_manager) -> None:
    """
    Create a rest exchange if a CCXTExchange matching class is found
    :param exchange_manager: the related exchange manager
    """
    rest_exchange_class = get_rest_exchange_class(exchange_manager.exchange_type,
                                                  exchange_manager.tentacles_setup_config)
    if rest_exchange_class:
        exchange_manager.exchange = rest_exchange_class(config=exchange_manager.config,
                                                        exchange_type=exchange_manager.exchange_type,
                                                        exchange_manager=exchange_manager,
                                                        is_sandboxed=exchange_manager.is_sandboxed)


async def _search_and_create_spot_exchange(exchange_manager) -> None:
    """
    Create a spot exchange if a SpotExchange matching class is found
    :param exchange_manager: the related exchange manager
    """
    spot_exchange_class = get_spot_exchange_class(exchange_manager.exchange_type,
                                                  exchange_manager.tentacles_setup_config)
    if spot_exchange_class:
        exchange_manager.exchange = spot_exchange_class(config=exchange_manager.config,
                                                        exchange_type=exchange_manager.exchange_type,
                                                        exchange_manager=exchange_manager,
                                                        is_sandboxed=exchange_manager.is_sandboxed)


async def _search_and_create_margin_exchange(exchange_manager) -> None:
    """
    Create a margin exchange if a MarginExchange matching class is found
    :param exchange_manager: the related exchange manager
    """
    margin_exchange_class = get_margin_exchange_class(exchange_manager.exchange_type,
                                                      exchange_manager.tentacles_setup_config)
    if margin_exchange_class:
        exchange_manager.exchange = margin_exchange_class(config=exchange_manager.config,
                                                          exchange_type=exchange_manager.exchange_type,
                                                          exchange_manager=exchange_manager,
                                                          is_sandboxed=exchange_manager.is_sandboxed)


async def _search_and_create_future_exchange(exchange_manager) -> None:
    """
    Create a future exchange if a FutureExchange matching class is found
    :param exchange_manager: the related exchange manager
    """
    future_exchange_class = get_future_exchange_class(exchange_manager.exchange_type,
                                                      exchange_manager.tentacles_setup_config)
    if future_exchange_class:
        exchange_manager.exchange = future_exchange_class(config=exchange_manager.config,
                                                          exchange_type=exchange_manager.exchange_type,
                                                          exchange_manager=exchange_manager,
                                                          is_sandboxed=exchange_manager.is_sandboxed)


def _initialize_simulator_time_frames(exchange_manager):
    """
    Initialize simulator client time frames
    :param exchange_manager: the related exchange manager
    """
    exchange_manager.client_time_frames = exchange_manager.exchange.get_available_time_frames()
