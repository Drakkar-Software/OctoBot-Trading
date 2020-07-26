# Drakkar-Software OctoBot-Trading
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
from octobot_tentacles_manager.api.configurator import get_class_from_name_with_activated_required_tentacles
from octobot_trading.exchanges.types.websocket_exchange import WebsocketExchange
from octobot_trading.constants import CONFIG_EXCHANGES, CONFIG_EXCHANGE_WEB_SOCKET


def force_disable_web_socket(config, exchange_name) -> bool:
    return CONFIG_EXCHANGE_WEB_SOCKET in config[CONFIG_EXCHANGES][exchange_name] \
           and not config[CONFIG_EXCHANGES][exchange_name][CONFIG_EXCHANGE_WEB_SOCKET]


def check_web_socket_config(config, exchange_name) -> bool:
    return not force_disable_web_socket(config, exchange_name)


def search_websocket_class(websocket_class, exchange_name, tentacles_setup_config):
    for socket_manager in websocket_class.__subclasses__():
        # return websocket exchange if available
        if socket_manager.has_name(exchange_name, tentacles_setup_config):
            return socket_manager
    return None


def get_exchange_websocket_from_name(name, tentacles_setup_config):
    return get_class_from_name_with_activated_required_tentacles(name, WebsocketExchange, tentacles_setup_config)
