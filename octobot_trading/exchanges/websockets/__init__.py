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
from octobot_websockets.feeds.bitmex import Bitmex

from octobot_trading.exchanges.websockets.abstract_websocket import AbstractWebSocket
from octobot_trading.exchanges.websockets.octobot_websocket import OctoBotWebSocketClient

WEBSOCKET_CLASSES = {
    "bitmex": Bitmex,
}


def get_websocket_client(config, exchange_manager):
    return OctoBotWebSocketClient(config, exchange_manager)
