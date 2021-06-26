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
import octobot_trading.constants
import octobot_trading.exchanges as exchanges


def is_exchange_managed_by_websocket(exchange_manager, channel):
    """
    # TODO improve checker
    """
    return not exchange_manager.rest_only \
           and exchange_manager.has_websocket \
           and not exchange_manager.is_backtesting \
           and channel in octobot_trading.constants.WEBSOCKET_FEEDS_TO_TRADING_CHANNELS \
           and any([exchange_manager.exchange_web_socket.is_feed_available(feed)
                    for feed in octobot_trading.constants.WEBSOCKET_FEEDS_TO_TRADING_CHANNELS[channel]])


def is_websocket_feed_requiring_init(exchange_manager, channel):
    return any([exchange_manager.exchange_web_socket.is_feed_requiring_init(feed)
                for feed in octobot_trading.constants.WEBSOCKET_FEEDS_TO_TRADING_CHANNELS[channel]])


async def search_and_create_websocket(exchange_manager):
    socket_manager = exchanges.search_websocket_class(exchanges.WebSocketExchange, exchange_manager)
    if socket_manager is not None:
        await _create_websocket(exchange_manager, exchanges.WebSocketExchange.__name__, socket_manager)


async def _create_websocket(exchange_manager, websocket_class_name, socket_manager):
    try:
        exchange_manager.exchange_web_socket = socket_manager.get_websocket_client(exchange_manager.config,
                                                                                   exchange_manager)
        if exchange_manager.is_valid_account:
            await _init_websocket(exchange_manager)
            exchange_manager.logger.info(f"{socket_manager.get_name()} connected to "
                                         f"{exchange_manager.exchange.name.capitalize()}")
        else:
            exchange_manager.logger.error(f"Impossible to start websockets for "
                                          f"{exchange_manager.exchange.name.capitalize()}: "
                                          f"incompatible account. Your OctoBot will work normally but will be "
                                          f"limited to the {exchange_manager.exchange.name.capitalize()} REST API "
                                          f"which is slower and allows for less simultaneous traded pairs "
                                          f"because of the exchange's rate limit.")
            exchange_manager.exchange_web_socket = None
            exchange_manager.has_websocket = False
    except Exception as e:
        exchange_manager.logger.error(f"Fail to init websocket for {websocket_class_name} "
                                      f"({exchange_manager.exchange.name}): {e}")
        exchange_manager.exchange_web_socket = None
        exchange_manager.has_websocket = False
        raise e


async def _init_websocket(exchange_manager):
    await exchange_manager.exchange_web_socket.init_websocket(exchange_manager.exchange_config.traded_time_frames,
                                                              exchange_manager.exchange_config.traded_symbol_pairs,
                                                              exchange_manager.tentacles_setup_config)

    await exchange_manager.exchange_web_socket.start_sockets()

    exchange_manager.has_websocket = exchange_manager.exchange_web_socket.is_websocket_running
