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
from abc import abstractmethod
from asyncio import CancelledError
from datetime import datetime
from typing import List

import ccxt
import websockets
from ccxt.base.errors import BadSymbol
from ccxt.base.exchange import Exchange as ccxtExchange

from octobot_commons.constants import HOURS_TO_SECONDS
from octobot_commons.enums import TimeFrames
from octobot_commons.logging.logging_util import get_logger
from octobot_trading.channels.exchange_channel import get_chan
from octobot_trading.constants import WebsocketFeeds as Feeds


class WebsocketExchange:
    MAX_DELAY = HOURS_TO_SECONDS

    def __init__(self,
                 exchange_manager: object,
                 pairs: list = None,
                 channels: list = None,
                 api_key: str = None,
                 api_secret: str = None,
                 api_password: str = None,
                 time_frames: List[TimeFrames] = None,
                 book_interval: int = 1000,
                 timeout: int = 120,
                 timeout_interval: int = 5):
        self.logger = get_logger(self.__class__.__name__)

        self.exchange_manager = exchange_manager
        self.exchange = self.exchange_manager.exchange
        self.exchange_id = self.exchange_manager.id
        self.use_testnet = self.exchange_manager.is_sandboxed

        self.loop = asyncio.get_event_loop()

        self.api_key = api_key
        self.api_secret = api_secret
        self.api_password = api_password

        self.timeout = timeout
        self.timeout_interval = timeout_interval
        self.book_update_interval = book_interval
        self.updates = 0

        self.is_connected = False
        self.is_authenticated = False
        self.should_stop = False

        self.pairs = []
        self.channels = []
        self.time_frames = time_frames if time_frames is not None else []

        self.websocket = None
        self.ccxt_client = None
        self._watch_task = None
        self.websocket_task = None
        self.last_msg = datetime.utcnow()

        self._initialize(pairs, channels)

    def _initialize(self, pairs, channels):
        self.async_ccxt_client = self.get_ccxt_async_client()()
        self.ccxt_client = getattr(ccxt, self.get_name())()
        self.ccxt_client.load_markets()

        self.pairs = [self.get_exchange_pair(pair) for pair in pairs] if pairs else []
        self.channels = [self.feed_to_exchange(chan) for chan in channels] if channels else []

    def start(self):
        self.websocket_task = self.loop.run_until_complete(self._connect())

    async def _watch(self):
        if self.last_msg:
            if datetime.utcnow() - datetime.timedelta(seconds=self.timeout) > self.last_msg:
                self.logger.warning("No messages received within timeout, restarting connection")
                await self.reconnect()
        await asyncio.sleep(self.timeout_interval)

    async def _connect(self):
        delay: int = 1
        self._watch_task = None
        while not self.should_stop:
            # manage max delay
            if delay >= self.MAX_DELAY:
                delay = self.MAX_DELAY

            try:
                async with websockets.connect(self.get_ws_endpoint()
                                              if not self.use_testnet else self.get_ws_testnet_endpoint()) as websocket:
                    self.websocket = websocket
                    self.on_open()
                    self._watch_task = asyncio.create_task(self._watch())
                    # connection was successful, reset retry count and delay
                    delay = 1
                    if self.api_key and self.api_secret:
                        await self.do_auth()

                    await self.subscribe()
                    await self._handler()
            except (websockets.ConnectionClosed, ConnectionAbortedError, ConnectionResetError, CancelledError) as e:
                self.logger.warning(f"{self.get_name()} encountered connection issue ({e}) - reconnecting...")
                await asyncio.sleep(delay)
                delay *= 2
            except Exception as e:
                self.logger.error(f"{self.get_name()} encountered an exception ({e}), reconnecting...")
                await asyncio.sleep(delay)
                delay *= 2
                raise e

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

    async def push_to_channel(self, channel_name, **kwargs):
        try:
            asyncio.run_coroutine_threadsafe(
                get_chan(channel_name, self.exchange_id).get_internal_producer().push(**kwargs),
                asyncio.get_event_loop())
        except Exception as e:
            self.logger.error(f"Push to {channel_name} failed : {e}")

    async def reconnect(self):
        self.stop()
        await self._connect()

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
        self.logger.debug("Pong received")

    def on_close(self):
        self.logger.info('Closed')

    def on_error(self, error):
        self.logger.error(f"Error : {error}")

    def stop(self):
        self.websocket.close()

    def close(self):
        self.stop()
        self._watch_task.cancel()
        self.websocket_task.cancel()
        self.is_connected = False
        self.websocket.close()
        self.on_close()

    @abstractmethod
    async def do_auth(self):
        NotImplementedError("on_message is not implemented")

    @abstractmethod
    async def ping(self):
        NotImplementedError("on_message is not implemented")

    @abstractmethod
    async def _send_command(self, command, args=None):
        raise NotImplementedError("_send_command is not implemented")

    @abstractmethod
    async def on_message(self, message):
        raise NotImplemented("on_message is not implemented")

    @abstractmethod
    async def subscribe(self):
        raise NotImplemented("subscribe is not implemented")

    @classmethod
    def get_name(cls) -> str:
        raise NotImplemented("get_name is not implemented")

    @classmethod
    def get_ws_endpoint(cls) -> str:
        raise NotImplemented("get_ws_endpoint is not implemented")

    @classmethod
    def get_ws_testnet_endpoint(cls) -> str:
        raise NotImplemented("get_ws_testnet_endpoint is not implemented")

    @classmethod
    def get_endpoint(cls) -> str:
        raise NotImplemented("get_endpoint is not implemented")

    @classmethod
    def get_testnet_endpoint(cls):
        raise NotImplemented("get_testnet_endpoint is not implemented")

    @classmethod
    def get_ccxt_async_client(cls):
        raise NotImplemented("get_ccxt_async_client is not implemented")

    @classmethod
    def get_L2_book_feed(cls) -> str:
        raise NotImplemented("get_L2_book_feed is not implemented")

    @classmethod
    def get_L3_book_feed(cls) -> str:
        raise NotImplemented("get_L3_book_feed is not implemented")

    @classmethod
    def get_trades_feed(cls) -> str:
        raise NotImplemented("get_trades_feed is not implemented")

    @classmethod
    def get_ticker_feed(cls) -> str:
        raise NotImplemented("get_ticker_feed is not implemented")

    @classmethod
    def get_candle_feed(cls) -> str:
        raise NotImplemented("get_candle_feed is not implemented")

    @classmethod
    def get_kline_feed(cls) -> str:
        raise NotImplemented("get_kline_feed is not implemented")

    @classmethod
    def get_funding_feed(cls) -> str:
        raise NotImplemented("get_funding_feed is not implemented")

    @classmethod
    def get_portfolio_feed(cls) -> str:
        raise NotImplemented("get_portfolio_feed is not implemented")

    @classmethod
    def get_orders_feed(cls) -> str:
        raise NotImplemented("get_orders_feed is not implemented")

    @classmethod
    def get_position_feed(cls) -> str:
        raise NotImplemented("get_position_feed is not implemented")

    @classmethod
    def get_mark_price_feed(cls) -> str:
        raise NotImplemented("get_mark_price_feed is not implemented")

    @classmethod
    def get_execution_feed(cls) -> str:
        raise NotImplemented("get_execution_feed is not implemented")

    def fix_timestamp(self, ts):
        return ts

    def timestamp_normalize(self, ts):
        return ts

    @classmethod
    def get_feeds(cls) -> dict:
        return {
            Feeds.FUNDING: cls.get_funding_feed(),
            Feeds.MARK_PRICE: cls.get_mark_price_feed(),
            Feeds.L2_BOOK: cls.get_L2_book_feed(),
            Feeds.L3_BOOK: cls.get_L3_book_feed(),
            Feeds.TRADES: cls.get_trades_feed(),
            Feeds.CANDLE: cls.get_candle_feed(),
            Feeds.KLINE: cls.get_kline_feed(),
            Feeds.TICKER: cls.get_ticker_feed(),
            Feeds.POSITION: cls.get_position_feed(),
            Feeds.ORDERS: cls.get_orders_feed(),
            Feeds.TRADE: cls.get_execution_feed(),
            Feeds.PORTFOLIO: cls.get_portfolio_feed()
        }

    def feed_to_exchange(self, feed):
        ret: str = self.get_feeds()[feed]
        if ret == Feeds.UNSUPPORTED.value:
            self.logger.error("{} is not supported on {}".format(feed, self.get_name()))
            raise ValueError(f"{feed} is not supported on {self.get_name()}")
        return ret

    """
    CCXT methods
    """

    @classmethod
    def get_ccxt(cls) -> object:
        getattr(ccxt, cls.get_name())

    def get_pairs(self):
        return self.ccxt_client.symbols

    def get_pair_from_exchange(self, pair: str) -> str:
        try:
            return self.ccxt_client.market(pair)["symbol"]
        except BadSymbol:
            try:
                return self.ccxt_client.markets_by_id[pair]["symbol"]
            except KeyError:
                self.logger.error(f"Failed to get market of {pair}")
                return None

    def get_exchange_pair(self, pair: str) -> str:
        if pair in self.ccxt_client.symbols:
            try:
                return self.ccxt_client.market(pair)["id"]
            except KeyError:
                raise KeyError(f'{pair} is not supported on {self.get_name()}')
        else:
            raise ValueError(f'{pair} is not supported on {self.get_name()}')

    def safe_float(self, dictionary, key, default_value):
        return ccxtExchange.safe_float(dictionary, key, default_value)

    @staticmethod
    def _convert_seconds_to_time_frame(time_frame_seconds):
        return [tf for tf, tf_min in TimeFramesMinutes.items() if tf_min == time_frame_seconds / MINUTE_TO_SECONDS][0]

    @staticmethod
    def _convert_time_frame_minutes_to_seconds(time_frame):
        if isinstance(time_frame, TimeFramesMinutes.__class__):
            return time_frame.value * MINUTE_TO_SECONDS
        elif isinstance(time_frame, int):
            return time_frame * MINUTE_TO_SECONDS
        else:
            return time_frame
