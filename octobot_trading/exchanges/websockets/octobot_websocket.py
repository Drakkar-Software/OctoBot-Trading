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
import asyncio
from concurrent.futures.thread import ThreadPoolExecutor

from octobot_trading.enums import WebsocketFeeds
from octobot_trading.exchanges.websockets.abstract_websocket import AbstractWebsocket
from octobot_trading.exchanges.websockets.websockets_util import get_exchange_websocket_from_name


class OctoBotWebSocketClient(AbstractWebsocket):
    def __init__(self, config, exchange_manager):
        super().__init__(config, exchange_manager)
        self.exchange_manager = exchange_manager
        self.exchange_name = exchange_manager.exchange_name

        self.octobot_websockets = []
        self.octobot_websockets_tasks = []

        self.octobot_websockets_executors = None
        self.exchange_class = None

        self.trader_pairs = []
        self.time_frames = []

        self.channels = []
        self.handled_feeds = {}

        self.is_websocket_running = False
        self.is_websocket_authenticated = False

    async def init_websocket(self, time_frames, trader_pairs, tentacles_setup_config):
        self.exchange_class = get_exchange_websocket_from_name(self.exchange_manager.exchange_name,
                                                               self.exchange_manager.tentacles_setup_config)
        self.trader_pairs = trader_pairs
        self.time_frames = time_frames

        if self.trader_pairs:
            # unauthenticated
            await self.add_feed(WebsocketFeeds.TRADES)
            await self.add_feed(WebsocketFeeds.L2_BOOK)
            await self.add_feed(WebsocketFeeds.L3_BOOK)
            await self.add_feed(WebsocketFeeds.BOOK_TICKER)
            await self.add_feed(WebsocketFeeds.MINI_TICKER)
            await self.add_feed(WebsocketFeeds.TICKER)
            await self.add_feed(WebsocketFeeds.FUNDING)
            await self.add_feed(WebsocketFeeds.MARK_PRICE)
            await self.add_feed(WebsocketFeeds.LIQUIDATIONS)

            if self.time_frames:
                await self.add_feed(WebsocketFeeds.CANDLE)
                await self.add_feed(WebsocketFeeds.KLINE)

            # authenticated
            await self.add_feed(WebsocketFeeds.POSITION)
            await self.add_feed(WebsocketFeeds.PORTFOLIO)
            await self.add_feed(WebsocketFeeds.TRADE)
            await self.add_feed(WebsocketFeeds.ORDERS)

            # ensure feeds are added
            self._create_octobot_feed_feeds()
        else:
            self.logger.warning(f"{self.exchange_manager.exchange_name.title()}'s "
                                f"websocket has no symbol to feed")

    async def add_feed(self, feed_name):
        if self.is_feed_available(feed_name):
            self.channels.append(feed_name)
            self.handled_feeds[feed_name] = True
        else:
            self.handled_feeds[feed_name] = False
            self.logger.debug(f"{self.exchange_manager.exchange_name}'s websocket is not handling {feed_name.value}")

    def is_feed_available(self, feed):
        try:
            feed_available = self.exchange_class.get_exchange_feed(feed)
            return feed_available is not WebsocketFeeds.UNSUPPORTED.value
        except (KeyError, ValueError):
            return False

    def is_feed_requiring_init(self, feed):
        return self.exchange_class.is_feed_requiring_init(feed)

    def _create_octobot_feed_feeds(self):
        try:
            key, secret, password = self.exchange_manager.get_exchange_credentials(self.logger, self.exchange_name)
            self.octobot_websockets.append(
                self.exchange_class(exchange_manager=self.exchange_manager,
                                    pairs=self.trader_pairs,
                                    time_frames=self.time_frames,
                                    channels=self.channels,
                                    api_key=key,
                                    api_secret=secret,
                                    api_password=password))
        except ValueError as e:
            self.logger.exception(e, True, f"Fail to create feed : {e}")

    @classmethod
    def get_name(cls):
        return cls.__name__

    @classmethod
    def has_name(cls, name: str, tentacles_setup_config: object):
        return get_exchange_websocket_from_name(name, tentacles_setup_config) is not None

    async def start_sockets(self):
        if any(self.handled_feeds.values()):
            try:
                self.octobot_websockets_executors = ThreadPoolExecutor(
                    max_workers=len(self.octobot_websockets),
                    thread_name_prefix=f"{self.get_name()}-{self.exchange_name}-pool-executor")

                self.octobot_websockets_tasks = [
                    asyncio.get_event_loop().run_in_executor(self.octobot_websockets_executors, websocket.start)
                    for websocket in self.octobot_websockets]

                self.is_websocket_running = True
            except ValueError as e:
                self.logger.error(f"Failed to start websocket on {self.exchange_name} : {e}")

        if not self.is_websocket_running:
            self.logger.error(f"{self.exchange_manager.exchange_name.title()}'s "
                              f"websocket is not handling anything, it will not be started, ")

    async def wait_sockets(self):
        await asyncio.wait(self.octobot_websockets_tasks)

    async def close_and_restart_sockets(self):
        for websocket in self.octobot_websockets:
            await websocket.reconnect()

    async def stop_sockets(self):
        for websocket in self.octobot_websockets:
            websocket.stop()

    def is_handling(self, feed_name):
        return feed_name in self.handled_feeds[feed_name] and self.handled_feeds[feed_name]

    @staticmethod
    def get_websocket_client(config, exchange_manager):
        return OctoBotWebSocketClient(config, exchange_manager)
