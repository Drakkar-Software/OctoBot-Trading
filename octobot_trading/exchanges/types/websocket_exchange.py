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
import concurrent.futures as futures

import octobot_commons.thread_util as thread_util
import octobot_trading.enums
import octobot_trading.exchanges.abstract_websocket_exchange as abstract_websocket
import octobot_trading.exchanges.connectors.abstract_websocket_connector as abstract_websocket_connector


class WebSocketExchange(abstract_websocket.AbstractWebsocketExchange):
    def __init__(self, config, exchange_manager):
        super().__init__(config, exchange_manager)
        self.exchange_manager = exchange_manager
        self.exchange_name = exchange_manager.exchange_name

        self.websocket_connectors = []
        self.websocket_connectors_tasks = []

        self.websocket_connectors_executors = None
        self.websocket_connector = None

        self.pairs = []
        self.time_frames = []

        self.channels = []
        self.handled_feeds = {}

        self.is_websocket_running = False
        self.is_websocket_authenticated = False

        self.restart_task = None

    async def init_websocket(self, time_frames, trader_pairs, tentacles_setup_config):
        self.websocket_connector = self.get_exchange_connector_class(self.exchange_manager)
        self.pairs = trader_pairs
        self.time_frames = time_frames

        if self.pairs:
            # unauthenticated
            await self.add_feed(octobot_trading.enums.WebsocketFeeds.TRADES)
            await self.add_feed(octobot_trading.enums.WebsocketFeeds.L2_BOOK)
            await self.add_feed(octobot_trading.enums.WebsocketFeeds.L3_BOOK)
            await self.add_feed(octobot_trading.enums.WebsocketFeeds.BOOK_DELTA)
            await self.add_feed(octobot_trading.enums.WebsocketFeeds.BOOK_TICKER)
            await self.add_feed(octobot_trading.enums.WebsocketFeeds.OPEN_INTEREST)
            await self.add_feed(octobot_trading.enums.WebsocketFeeds.MINI_TICKER)
            await self.add_feed(octobot_trading.enums.WebsocketFeeds.TICKER)
            await self.add_feed(octobot_trading.enums.WebsocketFeeds.FUNDING)
            await self.add_feed(octobot_trading.enums.WebsocketFeeds.MARK_PRICE)
            await self.add_feed(octobot_trading.enums.WebsocketFeeds.VOLUME)
            await self.add_feed(octobot_trading.enums.WebsocketFeeds.LIQUIDATIONS)
            await self.add_feed(octobot_trading.enums.WebsocketFeeds.FUTURES_INDEX)

            if self.time_frames:
                await self.add_feed(octobot_trading.enums.WebsocketFeeds.CANDLE)
                await self.add_feed(octobot_trading.enums.WebsocketFeeds.KLINE)

            # authenticated
            await self.add_feed(octobot_trading.enums.WebsocketFeeds.POSITION)
            await self.add_feed(octobot_trading.enums.WebsocketFeeds.PORTFOLIO)
            await self.add_feed(octobot_trading.enums.WebsocketFeeds.TRADE)
            await self.add_feed(octobot_trading.enums.WebsocketFeeds.ORDERS)

            # ensure feeds are added
            self.create_feeds()
        else:
            self.logger.warning(f"{self.exchange_manager.exchange_name.title()}'s "
                                f"websocket has no symbol to feed")

    async def add_feed(self, feed_name):
        if self.is_feed_available(feed_name):
            self.channels.append(feed_name)
            self.handled_feeds[feed_name] = True
            self.logger.debug(f"{self.exchange_manager.exchange_name}'s websocket is handling {feed_name.value}")
        else:
            self.handled_feeds[feed_name] = False
            self.logger.debug(f"{self.exchange_manager.exchange_name}'s websocket is not handling {feed_name.value}")

    def is_feed_available(self, feed):
        try:
            feed_available = self.websocket_connector.get_exchange_feed(feed)
            return feed_available is not octobot_trading.enums.WebsocketFeeds.UNSUPPORTED.value
        except (KeyError, ValueError):
            return False

    def is_feed_requiring_init(self, feed):
        return self.websocket_connector.is_feed_requiring_init(feed)

    @classmethod
    def get_name(cls):
        return cls.__name__

    @classmethod
    def has_name(cls, exchange_manager: object) -> bool:  # pylint: disable=arguments-renamed
        return cls.get_exchange_connector_class(exchange_manager) is not None

    def create_feeds(self):
        raise NotImplementedError("create_feeds is not implemented")

    @classmethod
    def get_exchange_connector_class(cls, exchange_manager: object):
        raise NotImplementedError("get_exchange_connector_class is not implemented")

    @staticmethod
    def get_websocket_client(config, exchange_manager):
        raise NotImplementedError("get_websocket_client is not implemented")

    @classmethod
    def get_class_method_name_to_get_compatible_websocket(cls, exchange_manager: object) -> str:
        if exchange_manager.is_future:
            return abstract_websocket_connector.AbstractWebsocketConnector.is_handling_future.__name__
        if exchange_manager.is_margin:
            return abstract_websocket_connector.AbstractWebsocketConnector.is_handling_margin.__name__
        return abstract_websocket_connector.AbstractWebsocketConnector.is_handling_spot.__name__

    async def start_sockets(self):
        if any(self.handled_feeds.values() and self.websocket_connectors):
            try:
                self.websocket_connectors_executors = futures.ThreadPoolExecutor(
                    max_workers=len(self.websocket_connectors),
                    thread_name_prefix=f"{self.get_name()}-{self.exchange_name}-pool-executor")

                self.websocket_connectors_tasks = [
                    asyncio.get_event_loop().run_in_executor(self.websocket_connectors_executors, websocket.start)
                    for websocket in self.websocket_connectors]

                self.is_websocket_running = True
            except ValueError as e:
                self.logger.error(f"Failed to start websocket on {self.exchange_name} : {e}")

        if self.websocket_connectors and not self.is_websocket_running:
            self.logger.debug(f"{self.exchange_manager.exchange_name.title()}'s "
                              f"websocket is not handling anything, it will not be started.")

    async def wait_sockets(self):
        await asyncio.wait(self.websocket_connectors_tasks)

    async def _inner_close_and_restart_sockets(self, debounce_duration):
        # asyncio.sleep to make it easily cancellable to reschedule later calls
        await asyncio.sleep(debounce_duration)
        for websocket in self.websocket_connectors:
            await websocket.reset()

    async def close_and_restart_sockets(self, debounce_duration=0):
        if self.restart_task is not None and not self.restart_task.done():
            self.restart_task.cancel()
        self.restart_task = asyncio.create_task(self._inner_close_and_restart_sockets(debounce_duration))

    async def stop_sockets(self):
        try:
            for websocket in self.websocket_connectors:
                await websocket.stop()
        except Exception as e:
            self.logger.error(f"Error when stopping sockets : {e}")

    async def close_sockets(self):
        try:
            for websocket in self.websocket_connectors:
                await websocket.close()
        except Exception as e:
            self.logger.error(f"Error when closing sockets : {e}")
        for websocket_task in self.websocket_connectors_tasks:
            websocket_task.cancel()
        thread_util.stop_thread_pool_executor_non_gracefully(self.websocket_connectors_executors)
        self.websocket_connectors_executors = None

    def add_pairs(self, pairs, watching_only=False):
        for websocket in self.websocket_connectors:
            websocket.add_pairs(pairs, watching_only=watching_only)

    def is_handling(self, feed_name):
        return feed_name in self.handled_feeds[feed_name] and self.handled_feeds[feed_name]

    def clear(self):
        super(WebSocketExchange, self).clear()
        for connector in self.websocket_connectors:
            connector.clear()
