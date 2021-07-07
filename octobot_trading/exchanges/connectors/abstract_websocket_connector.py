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
import abc
import asyncio
import logging
from datetime import datetime, timedelta

import time
import websockets

import octobot_commons.constants
import octobot_commons.enums
import octobot_commons.logging as commons_logging
import octobot_trading.exchanges.abstract_websocket_exchange as abstract_websocket


class AbstractWebsocketConnector(abstract_websocket.AbstractWebsocketExchange):
    LOGGERS = ["websockets.client", "websockets.server", "websockets.protocol"]
    MAX_DELAY = octobot_commons.constants.HOURS_TO_SECONDS
    EXCHANGE_FEEDS = {}
    INIT_REQUIRING_EXCHANGE_FEEDS = set()

    def __init__(self,
                 config: object,
                 exchange_manager: object,
                 timeout: int = 120,
                 timeout_interval: int = 5):
        super().__init__(config, exchange_manager)
        commons_logging.set_logging_level(self.LOGGERS, logging.WARNING)

        self.timeout = timeout
        self.timeout_interval = timeout_interval
        self.last_ping_time = 0

        # keyword arguments to be given to get_ws_endpoint
        self.endpoint_args = {}

        self.is_connected = False
        self.is_authenticated = False
        self.should_stop = False
        self.use_testnet = False

        self.websocket = None
        self._watch_task = None
        self.last_msg = datetime.utcnow()

    def start(self):
        asyncio.run(self._connect())

    async def _watcher(self):
        while True:
            if self.last_msg:
                if datetime.utcnow() - timedelta(seconds=self.timeout) > self.last_msg:
                    self.logger.warning("No messages received within timeout, restarting connection")
                    await self.reconnect()
            await self.ping()
            self.logger.debug("Sending keepalive...")
            await asyncio.sleep(self.timeout_interval)

    # pylint: disable=E1101
    # We need to ignore pylint E1101 (no-member) because of websockets legacy aliases
    async def _connect(self):
        delay: int = 1
        self._watch_task = None
        while not self.should_stop:
            # manage max delay
            if delay >= self.MAX_DELAY:
                delay = self.MAX_DELAY
            try:
                await self.before_connect()
            except Exception as e:
                self.logger.exception(e, True, f"Error on before_connect {e}")
            try:
                async with websockets.connect(self.get_ws_endpoint(**self.endpoint_args)
                                              if not self.use_testnet else self.get_ws_testnet_endpoint(),
                                              subprotocols=self.get_sub_protocol()) as websocket:
                    self.websocket = websocket
                    self.on_open()
                    self._watch_task = asyncio.create_task(self._watcher())
                    # connection was successful, reset delay
                    delay = 1
                    if self._should_authenticate():
                        await self.do_auth()

                    await self.prepare()
                    await self.subscribe()
                    await self._handler()
            except (websockets.ConnectionClosed, ConnectionAbortedError,
                    ConnectionResetError, asyncio.CancelledError) as e:
                self.logger.warning(f"{self.get_name()} encountered connection issue ({e}) - reconnecting...")
            except Exception as e:
                self.logger.exception(e, True, f"{self.get_name()} encountered an exception ({e}), reconnecting...")
            await asyncio.sleep(delay)
            delay *= 2

    async def _handler(self):
        async for message in self.websocket:
            self.last_msg = datetime.utcnow()
            try:
                await self.on_message(message)
            except Exception:
                self.logger.error(f"{self.get_name()}: error handling message {message}")
                # exception will be logged with traceback when connection handler
                # retries the connection
                raise

    async def reconnect(self):
        self.stop()
        await self._connect()

    async def reset(self):
        await self.reconnect()

    def on_open(self):
        self.logger.info("Connected")

    def on_auth(self, status):
        if status:
            self.is_authenticated = True
            self.logger.info("Authenticated")
        else:
            self.is_authenticated = False
            self.logger.warning("Authentication failed")

    def on_pong(self):
        self.logger.debug(f"Pong received | latency = {float(time.time() * 1000)  - (self.last_ping_time * 1000)}")

    async def on_ping(self):
        self.logger.debug("Ping received. Sending pong...")
        await self.websocket.pong()

    async def ping(self):
        self.last_ping_time = time.time()
        await self.websocket.ping()

    def on_close(self):
        self.logger.info('Closed')

    def on_error(self, error):
        self.logger.error(f"Error : {error}")

    async def stop(self):
        self.websocket.close()
        self.exchange_manager = None

    async def close(self):
        await self.stop()
        self._watch_task.cancel()
        self.is_connected = False
        self.websocket.close()
        self.on_close()
        self.websocket = None

    async def before_connect(self):
        pass

    async def prepare(self):
        pass

    def get_sub_protocol(self):
        return []

    @abc.abstractmethod
    async def _send_command(self, command, args=None):
        raise NotImplementedError("_send_command is not implemented")

    @abc.abstractmethod
    async def on_message(self, message):
        raise NotImplementedError("on_message is not implemented")

    @classmethod
    def get_ws_endpoint(cls) -> str:
        raise NotImplementedError("get_ws_endpoint is not implemented")

    @classmethod
    def get_ws_testnet_endpoint(cls) -> str:
        raise NotImplementedError("get_ws_testnet_endpoint is not implemented")

    @classmethod
    def get_endpoint(cls) -> str:
        raise NotImplementedError("get_endpoint is not implemented")

    @classmethod
    def get_testnet_endpoint(cls):
        raise NotImplementedError("get_testnet_endpoint is not implemented")
