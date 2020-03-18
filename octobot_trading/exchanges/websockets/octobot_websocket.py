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

from octobot_commons.constants import MINUTE_TO_SECONDS
from octobot_commons.enums import TimeFramesMinutes
from octobot_trading.channels.exchange_channel import get_chan
from octobot_trading.constants import RECENT_TRADES_CHANNEL, ORDER_BOOK_CHANNEL, TICKER_CHANNEL, KLINE_CHANNEL, \
    OHLCV_CHANNEL, MARK_PRICE_CHANNEL, FUNDING_CHANNEL, POSITIONS_CHANNEL, BALANCE_CHANNEL, ORDERS_CHANNEL, \
    TRADES_CHANNEL
from octobot_trading.exchanges.websockets.abstract_websocket import AbstractWebsocket
from octobot_trading.exchanges.websockets.websocket_callbacks import RecentTradesCallBack, OrderBookCallBack, \
    TickersCallBack, KlineCallBack, OHLCVCallBack, MarkPriceCallBack, FundingCallBack, PositionsCallBack, \
    BalanceCallBack, ExecutionsCallBack, OrdersCallBack
from octobot_websockets.api.feed_creator import get_feed_from_name
from octobot_websockets.feeds.feed import Feeds


class OctoBotWebSocketClient(AbstractWebsocket):
    CF_MARKET_SEPARATOR = "-"

    def __init__(self, config, exchange_manager):
        super().__init__(config, exchange_manager)
        self.exchange_manager = exchange_manager
        self.exchange_name = exchange_manager.exchange_name
        self.octobot_websockets = []
        self.octobot_websockets_t = []
        self.octobot_websockets_executors = None

        self.open_sockets_keys = {}
        self.exchange_class = None

        self.trader_pairs = []
        self.time_frames = []

        self.channels = []
        self.callbacks = {}
        self.handled_feeds = {}

        self.is_websocket_running = False
        self.is_websocket_authenticated = False
        self.use_separated_websockets = False

    async def init_web_sockets(self, time_frames, trader_pairs):
        self.exchange_class = get_feed_from_name(self.exchange_manager.exchange_name)
        self.trader_pairs = trader_pairs
        self.time_frames = time_frames

        if self.trader_pairs:
            # unauthenticated
            await self.add_feed(RecentTradesCallBack, Feeds.TRADES, RECENT_TRADES_CHANNEL, self.trader_pairs)
            await self.add_feed(OrderBookCallBack, Feeds.L2_BOOK, ORDER_BOOK_CHANNEL, self.trader_pairs)
            await self.add_feed(OrderBookCallBack, Feeds.L3_BOOK, ORDER_BOOK_CHANNEL, self.trader_pairs)
            await self.add_feed(TickersCallBack, Feeds.TICKER, TICKER_CHANNEL, self.trader_pairs)
            await self.add_feed(FundingCallBack, Feeds.FUNDING, FUNDING_CHANNEL, self.trader_pairs)
            await self.add_feed(MarkPriceCallBack, Feeds.MARK_PRICE, MARK_PRICE_CHANNEL, self.trader_pairs)

            if self.time_frames:
                await self.add_feed(OHLCVCallBack, Feeds.CANDLE, OHLCV_CHANNEL, self.trader_pairs, self.time_frames)
                await self.add_feed(KlineCallBack, Feeds.KLINE, KLINE_CHANNEL, self.trader_pairs, self.time_frames)

            # authenticated
            await self.add_feed(PositionsCallBack, Feeds.POSITION, POSITIONS_CHANNEL)
            await self.add_feed(BalanceCallBack, Feeds.PORTFOLIO, BALANCE_CHANNEL)
            await self.add_feed(ExecutionsCallBack, Feeds.TRADE, TRADES_CHANNEL)
            await self.add_feed(OrdersCallBack, Feeds.ORDERS, ORDERS_CHANNEL)

            # ensure feeds are added
            self.__create_octobot_feed_feeds()
        else:
            self.logger.warning(f"{self.exchange_manager.exchange_name.title()}'s "
                                f"websocket has no symbol to feed")

    async def add_feed(self, callback_class, feed_name, channel_name, symbols=None, time_frames=None):
        if self.is_feed_available(feed_name):
            if symbols:
                if time_frames:
                    await self.add_time_frames_feeds(callback_class, feed_name, channel_name, symbols, time_frames)
                else:
                    await self.add_symbols_feeds(callback_class, feed_name, channel_name, symbols)
            else:
                callback = callback_class(self, get_chan(channel_name, self.exchange_manager.id))
                self._add_callback(callback.callback, feed_name)
                await self._run_callback(feed_name, callback)

            self.handled_feeds[feed_name] = True
        else:
            self.handled_feeds[feed_name] = False
            self.logger.warning(f"{self.exchange_manager.exchange_name}'s "
                                f"websocket is not handling {feed_name.value}")

    async def add_symbols_feeds(self, callback_class, feed_name, channel_name, symbols):
        for symbol in symbols:
            callback = callback_class(self,
                                      get_chan(channel_name, self.exchange_manager.id),
                                      pair=symbol)
            self._add_callback(callback.callback, feed_name, symbol=symbol)
            await self._run_callback(feed_name, callback)

    async def add_time_frames_feeds(self, callback_class, feed_name, channel_name, symbols, time_frames):
        for symbol in symbols:
            for time_frame in time_frames:
                callback = callback_class(self,
                                          get_chan(channel_name, self.exchange_manager.id),
                                          pair=symbol,
                                          time_frame=time_frame)
                self._add_callback(callback.callback, feed_name, symbol=symbol, time_frame=time_frame)
                await self._run_callback(feed_name, callback)

    async def _run_callback(self, feed, callback):
        if self.use_separated_websockets:
            # TODO
            # should run and reset channels (duplicate)
            # if feed in self.channels:
            #     self.__create_octobot_feed_feeds()
            #     self.channels = []
            #     self.callbacks = {}
            pass

        self.channels.append(feed)
        await callback.run()

    def _add_callback(self, callback, feed_name, symbol=None, time_frame=None):
        if symbol:
            if feed_name not in self.callbacks:
                self.callbacks[feed_name] = {}
            if time_frame:
                if symbol not in self.callbacks[feed_name]:
                    self.callbacks[feed_name][symbol] = {}
                self.callbacks[feed_name][symbol][time_frame] = callback
            else:
                self.callbacks[feed_name][symbol] = callback
        else:
            self.callbacks[feed_name] = callback

    def is_feed_available(self, feed):
        try:
            feed_available = self.exchange_class.get_feeds()[feed]
            return feed_available is not Feeds.UNSUPPORTED.value
        except (KeyError, ValueError):
            return False

    def __create_octobot_feed_feeds(self):
        try:
            key, secret, password = self.exchange_manager.get_exchange_credentials(self.logger, self.exchange_name)
            self.octobot_websockets.append(
                self.exchange_class(pairs=self.trader_pairs,
                                    time_frames=self.time_frames,
                                    channels=self.channels,
                                    callbacks=self.callbacks,
                                    api_key=key,
                                    api_secret=secret,
                                    api_password=password,
                                    use_testnet=self.exchange_manager.is_sandboxed))
        except ValueError as e:
            self.logger.exception(e, True, f"Fail to create feed : {e}")

    @classmethod
    def get_name(cls):
        return cls.__name__

    @classmethod
    def has_name(cls, name: str):
        return get_feed_from_name(name) is not None

    def start_sockets(self):
        if any(self.handled_feeds.values()):
            try:
                self.octobot_websockets_executors = ThreadPoolExecutor(
                    max_workers=len(self.octobot_websockets),
                    thread_name_prefix=f"{self.get_name()}-{self.exchange_name}-pool-executor")
                for websocket in self.octobot_websockets:
                    asyncio.get_event_loop().run_in_executor(self.octobot_websockets_executors, websocket.start)
                self.is_websocket_running = True
            except ValueError as e:
                self.logger.error(f"Failed to start websocket on {self.exchange_name} : {e}")

        if not self.is_websocket_running:
            self.logger.error(f"{self.exchange_manager.exchange_name.title()}'s "
                              f"websocket is not handling anything, it will not be started, ")

    def close_and_restart_sockets(self):
        # TODO
        pass

    def stop_sockets(self):
        pass

    def handles_recent_trades(self):
        return self.is_handling_recent_trades  # TODO implement dynamicaly

    def handles_order_book(self):
        return self.is_handling_order_book  # TODO implement dynamicaly

    def handles_price_ticker(self):
        return self.is_handling_price_ticker  # TODO implement dynamicaly

    def handles_funding(self):
        return False

    def handles_mark_price(self):
        return False

    def handles_ohlcv(self):
        return False

    def handles_balance(self):
        return False

    def handles_orders(self):
        return False

    def handles_positions(self):
        return False

    def handles_executions(self):
        return False

    @staticmethod
    def __convert_seconds_to_time_frame(time_frame_seconds):
        return [tf for tf, tf_min in TimeFramesMinutes.items() if tf_min == time_frame_seconds / MINUTE_TO_SECONDS][0]

    @staticmethod
    def __convert_time_frame_minutes_to_seconds(time_frame):
        if isinstance(time_frame, TimeFramesMinutes.__class__):
            return time_frame.value * MINUTE_TO_SECONDS
        elif isinstance(time_frame, int):
            return time_frame * MINUTE_TO_SECONDS
        else:
            return time_frame

    @staticmethod
    def get_websocket_client(config, exchange_manager):
        return OctoBotWebSocketClient(config, exchange_manager)

    @staticmethod
    def parse_order_status(status):
        pass
