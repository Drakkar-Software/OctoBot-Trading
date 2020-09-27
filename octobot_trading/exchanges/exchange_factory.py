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

import octobot_trading.errors as errors
import octobot_trading.exchanges as exchanges


async def create_exchanges(exchange_manager):
    if exchange_manager.is_sandboxed:
        exchange_manager.logger.info(f"Using sandbox exchange for {exchange_manager.exchange_name}")

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
        await exchanges.create_exchange_producers(exchange_manager)

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
    except errors.AuthenticationError:
        exchange_manager.logger.error("Authentication error, retrying without authentication...")
        exchange_manager.without_auth = True
        await create_real_exchange(exchange_manager)
        return


async def initialize_real_exchange(exchange_manager):
    if not exchange_manager.exchange_only:
        await exchanges.create_exchange_channels(exchange_manager)

    # create Websocket exchange if possible
    if not exchange_manager.rest_only:
        # search for websocket
        if exchanges.check_web_socket_config(exchange_manager.config, exchange_manager.exchange.name):
            await exchanges.search_and_create_websocket(exchange_manager)


async def _create_rest_exchange(exchange_manager) -> None:
    """
    create REST based on ccxt exchange
    :param exchange_manager: the related exchange manager
    """
    if exchange_manager.is_future and not exchange_manager.is_spot_only:
        await _search_and_create_future_exchange(exchange_manager)
    elif exchange_manager.is_margin and not exchange_manager.is_spot_only:
        await _search_and_create_margin_exchange(exchange_manager)
    else:
        await _search_and_create_spot_exchange(exchange_manager)

    if not exchange_manager.exchange:
        raise Exception("Can't create an exchange instance that match the exchange configuration")


async def create_simulated_exchange(exchange_manager):
    if exchange_manager.is_future and not exchange_manager.is_spot_only:
        exchange_manager.exchange = exchanges.FutureExchangeSimulator(exchange_manager.config, exchange_manager,
                                                                      exchange_manager.backtesting)
    elif exchange_manager.is_margin and not exchange_manager.is_spot_only:
        exchange_manager.exchange = exchanges.MarginExchangeSimulator(exchange_manager.config, exchange_manager,
                                                                      exchange_manager.backtesting)
    else:
        exchange_manager.exchange = exchanges.SpotExchangeSimulator(exchange_manager.config, exchange_manager,
                                                                    exchange_manager.backtesting)

    await exchange_manager.exchange.initialize()
    _initialize_simulator_time_frames(exchange_manager)
    exchange_manager.exchange_config.set_config_time_frame()
    exchange_manager.exchange_config.set_config_traded_pairs()
    await exchanges.create_exchange_channels(exchange_manager)


async def init_simulated_exchange(exchange_manager):
    await exchange_manager.exchange.create_backtesting_exchange_producers()


async def _search_and_create_spot_exchange(exchange_manager) -> None:
    """
    Create a spot exchange if a SpotExchange matching class is found
    :param exchange_manager: the related exchange manager
    """
    spot_exchange_class = exchanges.get_spot_exchange_class(exchange_manager.exchange_name,
                                                            exchange_manager.tentacles_setup_config)
    if spot_exchange_class:
        exchange_manager.exchange = spot_exchange_class(config=exchange_manager.config,
                                                        exchange_manager=exchange_manager)


async def _search_and_create_margin_exchange(exchange_manager) -> None:
    """
    Create a margin exchange if a MarginExchange matching class is found
    :param exchange_manager: the related exchange manager
    """
    margin_exchange_class = exchanges.get_margin_exchange_class(exchange_manager.exchange_name,
                                                                exchange_manager.tentacles_setup_config)
    if margin_exchange_class:
        exchange_manager.exchange = margin_exchange_class(config=exchange_manager.config,
                                                          exchange_manager=exchange_manager)


async def _search_and_create_future_exchange(exchange_manager) -> None:
    """
    Create a future exchange if a FutureExchange matching class is found
    :param exchange_manager: the related exchange manager
    """
    future_exchange_class = exchanges.get_future_exchange_class(exchange_manager.exchange_name,
                                                                exchange_manager.tentacles_setup_config)
    if future_exchange_class:
        exchange_manager.exchange = future_exchange_class(config=exchange_manager.config,
                                                          exchange_manager=exchange_manager)


def _initialize_simulator_time_frames(exchange_manager):
    """
    Initialize simulator client time frames
    :param exchange_manager: the related exchange manager
    """
    exchange_manager.client_time_frames = exchange_manager.exchange.get_available_time_frames()
