# pylint: disable=E0611
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

from abc import abstractmethod, ABCMeta

from octobot_commons.logging.logging_util import get_logger


class AbstractWebsocket:
    __metaclass__ = ABCMeta

    def __init__(self, config, exchange_manager):
        self.config = config
        self.exchange_manager = exchange_manager
        self.client = None
        self.name = self.get_name()
        self.logger = get_logger(f"WebSocket - {self.name}")

    # Abstract methods
    @classmethod
    def get_name(cls):
        raise NotImplementedError("get_name not implemented")

    @classmethod
    def has_name(cls, name: str) -> bool:
        raise NotImplementedError("has_name not implemented")

    @staticmethod
    def get_websocket_client(config, exchange_manager):
        raise NotImplementedError("get_websocket_client not implemented")

    @abstractmethod
    def is_handling(self, feed_name):
        raise NotImplementedError("is_handling not implemented")

    @abstractmethod
    async def init_websocket(self, time_frames, trader_pairs, tentacles_setup_config):
        raise NotImplementedError("init_websocket not implemented")

    @abstractmethod
    async def start_sockets(self):
        raise NotImplementedError("start_sockets not implemented")

    @abstractmethod
    async def wait_sockets(self):
        raise NotImplementedError("wait_sockets not implemented")

    @abstractmethod
    async def close_and_restart_sockets(self):
        raise NotImplementedError("close_and_restart_sockets not implemented")

    @abstractmethod
    async def stop_sockets(self):
        raise NotImplementedError("stop_sockets not implemented")
