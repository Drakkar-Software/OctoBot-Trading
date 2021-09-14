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
import logging
import os
import threading

import cryptofeed
import cryptofeed.connection_handler
import cryptofeed.callback as cryptofeed_callbacks
import cryptofeed.config as cryptofeed_config
import cryptofeed.defines as cryptofeed_constants
import cryptofeed.exchanges as cryptofeed_exchanges

import octobot_commons
import octobot_commons.asyncio_tools as asyncio_tools
import octobot_commons.enums as commons_enums
import octobot_commons.logging as commons_logging
import octobot_commons.symbol_util as symbol_util
import octobot_commons.time_frame_manager as time_frame_manager

import octobot_trading.constants as trading_constants
import octobot_trading.enums as trading_enums
import octobot_trading.exchanges.abstract_websocket_exchange as abstract_websocket
import octobot_trading.exchanges.connectors.abstract_websocket_connector as abstract_websocket_connector
from octobot_trading.enums import WebsocketFeeds as Feeds
from octobot_trading.enums import ExchangeConstantsOrderBookInfoColumns as ECOBIC, \
    ExchangeConstantsTickersColumns as Ectc


class CryptofeedWebsocketConnector(abstract_websocket.AbstractWebsocketExchange):
    CRYPTOFEED_LOGGERS = ["feedhandler"] + abstract_websocket_connector.AbstractWebsocketConnector.LOGGERS
    CRYPTOFEED_DEFAULT_MARKET_SEPARATOR = "-"

    INIT_REQUIRING_EXCHANGE_FEEDS = [Feeds.CANDLE]

    IGNORED_FEED_PAIRS = {
        Feeds.TRADES: [Feeds.TICKER],  # When ticker is available : no need to calculate mark price from recent trades
        Feeds.TICKER: [Feeds.CANDLE]  # When candles are available : use min timeframe kline to push ticker
    }

    CRYPTOFEED_FEEDS_TO_WEBSOCKET_FEEDS = {
        # Unauthenticated
        cryptofeed_constants.TRADES: Feeds.TRADES,
        cryptofeed_constants.TICKER: Feeds.TICKER,
        cryptofeed_constants.CANDLES: Feeds.CANDLE,
        cryptofeed_constants.L2_BOOK: Feeds.L2_BOOK,
        cryptofeed_constants.L3_BOOK: Feeds.L3_BOOK,
        cryptofeed_constants.FUNDING: Feeds.FUNDING,
        cryptofeed_constants.LIQUIDATIONS: Feeds.LIQUIDATIONS,
        cryptofeed_constants.BOOK_DELTA: Feeds.BOOK_DELTA,
        cryptofeed_constants.OPEN_INTEREST: Feeds.OPEN_INTEREST,
        cryptofeed_constants.FUTURES_INDEX: Feeds.FUTURES_INDEX,
        # cryptofeed_constants.LAST_PRICE: Feeds.LAST_PRICE,

        # Authenticated
        cryptofeed_constants.TRANSACTIONS: Feeds.TRANSACTIONS,
        cryptofeed_constants.BALANCES: Feeds.PORTFOLIO,
        # cryptofeed_constants.USER_DATA: None,
        cryptofeed_constants.PLACE_ORDER: Feeds.ORDERS,
        cryptofeed_constants.CANCEL_ORDER: Feeds.ORDERS,
        cryptofeed_constants.ORDER_STATUS: Feeds.ORDERS,
        cryptofeed_constants.ORDER_INFO: Feeds.ORDERS,
        cryptofeed_constants.TRADE_HISTORY: Feeds.TRADE,
        cryptofeed_constants.USER_FILLS: Feeds.TRADE,
    }

    CANDLE_CHANNELS = [
        cryptofeed_constants.CANDLES,
    ]
    WATCHED_PAIR_CHANNELS = [
        cryptofeed_constants.TRADES,
        cryptofeed_constants.TICKER,
        cryptofeed_constants.CANDLES,
    ]

    EXCHANGE_CONSTRUCTOR_KWARGS = {}

    def __init__(self, config: object, exchange_manager: object):
        super().__init__(config, exchange_manager)
        self.channels = []

        self.callbacks = {}
        self.candle_callback = None

        self.filtered_pairs = []
        self.watched_pairs = []
        self.filtered_timeframes = []
        self.min_timeframe = None

        self.local_loop = None
        self.is_websocket_restarting = False

        self._fix_signal_handler()

        # Manage cryptofeed loggers
        self.client_logger = logging.getLogger(f"WebSocketClient - {self.name}")
        self.client_logger.setLevel(logging.WARNING)
        self._fix_logger()

        self.client = None
        self.client_config = None
        commons_logging.set_logging_level(self.CRYPTOFEED_LOGGERS, logging.WARNING)

        self.callback_by_feed = {
            cryptofeed_constants.TRADES: cryptofeed_callbacks.TradeCallback(self.trades),
            cryptofeed_constants.TICKER: cryptofeed_callbacks.TickerCallback(self.ticker),
            cryptofeed_constants.CANDLES: cryptofeed_callbacks.CandleCallback(self.candle),
            # cryptofeed_constants.LAST_PRICE: cryptofeed_callbacks.LastPriceCallback(self.last_price),
            # cryptofeed_constants.L2_BOOK: cryptofeed_callbacks.BookCallback(self.book),
            # cryptofeed_constants.L3_BOOK: cryptofeed_callbacks.BookCallback(self.book),
            # cryptofeed_constants.FUNDING: cryptofeed_callbacks.FundingCallback(self.funding),
            # cryptofeed_constants.LIQUIDATIONS: cryptofeed_callbacks.LiquidationCallback(self.liquidations),
            # cryptofeed_constants.BOOK_DELTA: cryptofeed_callbacks.BookUpdateCallback(self.delta)
            # cryptofeed_constants.OPEN_INTEREST: cryptofeed_callbacks.OpenInterestCallback(self.open_interest),
            # cryptofeed_constants.FUTURES_INDEX: cryptofeed_callbacks.FuturesIndexCallback(self.futures_index),
            cryptofeed_constants.ORDER_INFO: cryptofeed_callbacks.OrderInfoCallback(self.order),
            # cryptofeed_constants.USER_FILLS: cryptofeed_callbacks.UserFillsCallback(self.trade),
            cryptofeed_constants.TRANSACTIONS: cryptofeed_callbacks.TransactionsCallback(self.transaction),
            cryptofeed_constants.BALANCES: cryptofeed_callbacks.BalancesCallback(self.balance),
            # cryptofeed_constants.USER_DATA: cryptofeed_callbacks.UserDataCallback(self.user_data),
        }
        self._set_async_callbacks()

        # Create cryptofeed FeedHandler instance
        self._create_client()

        # Creates cryptofeed exchange instance
        self.cryptofeed_exchange = cryptofeed_exchanges.EXCHANGE_MAP[self.get_feed_name()](
            config=self.client_config, **self.EXCHANGE_CONSTRUCTOR_KWARGS)

    """
    Abstract methods
    """

    @classmethod
    def get_feed_name(cls):
        raise NotImplementedError("get_feed_name not implemented")

    """
    Abstract implementations
    """

    def start(self):
        self._init_client()
        self._start_client()

    async def _inner_stop(self):
        try:
            for feed in self.client.feeds:
                feed.stop()
            for feed in self.client.feeds:
                await feed.shutdown()
            if self.client.raw_data_collection:
                self.client.raw_data_collection.stop()
        except Exception as e:
            self.logger.exception(e, False)
            self.logger.error(f"Failed to stop websocket feed : {e}")

    async def stop(self):
        """
        Reimplementation of self.client.stop() without calling loop.run_until_complete()
        """
        if asyncio.get_event_loop() is self.local_loop:
            await self._inner_stop()
        else:
            asyncio_tools.run_coroutine_in_asyncio_loop(self._inner_stop(), self.local_loop)

    async def close(self):
        """
        Can't call self.client.close() because it uses loop operations
        """
        try:
            self.client = None
        except Exception as e:
            self.logger.error(f"Failed to close websocket feed : {e}")

    def add_pairs(self, pairs, watching_only=False):
        """
        Add new pairs to self.filtered_pairs
        :param pairs: the list of pair to add
        :param watching_only: if pairs are for watching or trading purpose
        """
        for pair in pairs:
            self._add_pair(self.get_exchange_pair(pair), watching_only=watching_only)

    def add_time_frames(self, time_frames):
        """
        Add new time_frames to self.filtered_time_frames
        :param time_frames: the list of time_frame to add
        """
        for time_frame in time_frames:
            self._add_time_frame(time_frame)

    async def _inner_reset(self):
        """
        Removes and stops all running feeds an recreate them
        """
        try:
            self._remove_all_feeds()
            await self.stop()
            await self.close()

            self._create_client()
            if self.candle_callback is not None:
                self._subscribe_candle_feed()
            self._subscribe_pairs_feeds()
            self._start_client(should_create_loop=False)
        except Exception as e:
            self.logger.error(f"Failed to reconnect to websocket : {e}")

    def _call_inner_reset(self):
        self.is_websocket_restarting = True
        try:
            asyncio_tools.run_coroutine_in_asyncio_loop(self._inner_reset(), self.local_loop)
        except Exception as e:
            self.logger.exception(e, True, f"Error when resetting websockets {e}")
        finally:
            self.is_websocket_restarting = False

    async def reset(self):
        if self.is_websocket_restarting:
            self.logger.debug("Reset attempt but a reset is already in progress.")
            return
        # force is_websocket_restarting here also to avoid multithreading issues
        self.is_websocket_restarting = True
        # reset might take up to a few seconds, no need to wait for it and block the whole async loop
        threading.Thread(target=self._call_inner_reset, name=f"{self.name}ResetWrapper").start()

    @classmethod
    def is_supporting_exchange(cls, exchange_candidate_name) -> bool:
        return cls.get_name() == exchange_candidate_name

    def get_pair_from_exchange(self, pair):
        """
        Convert a cryptofeed symbol format to uniformized symbol format
        :param pair: the pair to format
        :return: the formatted pair when success else an empty string
        """
        try:
            return symbol_util.convert_symbol(
                symbol=pair,
                symbol_separator=self.CRYPTOFEED_DEFAULT_MARKET_SEPARATOR,
                new_symbol_separator=octobot_commons.MARKET_SEPARATOR,
                should_uppercase=True,
            )
        except Exception:
            self.logger.error(f"Failed to get market of {pair}")
        return ""

    def get_exchange_pair(self, pair) -> str:
        """
        Convert an uniformized symbol format to a cryptofeed symbol format
        :param pair: the pair to format
        :return: the cryptofeed pair when success else an empty string
        """
        try:
            return symbol_util.convert_symbol(
                symbol=pair,
                symbol_separator=octobot_commons.MARKET_SEPARATOR,
                new_symbol_separator=self.CRYPTOFEED_DEFAULT_MARKET_SEPARATOR,
                should_uppercase=True,
            )
        except Exception:
            self.logger.error(f"Failed to get market of {pair}")
        return ""

    """
    Private methods
    """

    def _create_client(self):
        """
        Creates cryptofeed client instance
        """
        self._create_client_config()
        self.client = cryptofeed.FeedHandler(config=self.client_config)

    def _create_client_config(self):
        """
        Creates cryptofeed config
        """
        self.client_config = cryptofeed_config.Config()
        try:
            # Disable cryptofeed log file
            self.client_config.config['log']['filename'] = os.devnull
            self.client_config.config['rest']['log']['filename'] = os.devnull
        except KeyError:
            pass
        self.client_config.config[self.get_feed_name().lower()] = self._get_credentials_config()

    def _get_credentials_config(self):
        """
        Add exchange credentials to FeedHandler client config
        """
        if self._should_use_authenticated_feeds():
            key_id, key_secret, key_passphrase = self.get_exchange_credentials()
            return {
                "key_id": key_id,
                "key_secret": key_secret,
                "key_passphrase": key_passphrase
            }
        return {}

    def _init_client(self):
        """
        Prepares client configuration and instantiates client feeds
        """
        try:
            self.client.config = self.client_config
            self._filter_exchange_pairs_and_timeframes()
            self._subscribe_feeds()
        except Exception as e:
            self.logger.exception(e, True, f"Failed to subscribe when creating websocket feed : {e}")

    def _start_client(self, should_create_loop=True):
        """
        Creates client async loop and start client
        :param should_create_loop: When True creates a new async loop. When False uses the current one
        """
        try:
            if should_create_loop:
                # without this two lines `There is no current event loop in thread`
                # is raised when calling `client.run()`
                self.local_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.local_loop)
            self.logger.debug(f"Starting websocket client with {len(self.client.feeds)} feeds.")
            self.client.run(start_loop=should_create_loop)
        except Exception as e:
            self.logger.error(f"Failed to start websocket feed : {e}")

    def _subscribe_feeds(self):
        """
        Prepares the subscription of unauthenticated and authenticated feeds and subscribe all
        """
        if self._should_run_candle_feed():
            self.candle_callback = self.callback_by_feed[self.EXCHANGE_FEEDS[Feeds.CANDLE]]
            self._subscribe_candle_feed()

        # drop unsupported channels
        self.channels = [channel for channel in self.channels
                         if self._is_supported_channel(channel)
                         and channel != self.EXCHANGE_FEEDS.get(Feeds.CANDLE)]

        self.callbacks = {
            channel: self.callback_by_feed[channel]
            for channel in self.channels
            if self.callback_by_feed.get(channel)
        }

        # Add candle callback to callbacks
        self.callbacks[self.EXCHANGE_FEEDS[Feeds.CANDLE]] = self.candle_callback

        self._subscribe_pairs_feeds()

    def _should_use_authenticated_feeds(self):
        """
        :return: True when authenticated feeds shouldn't be added
        """
        return self._should_authenticate() and self.exchange.authenticated() and not self.exchange_manager.is_sandboxed

    def _is_supported_channel(self, channel):
        """
        Checks if the channel is supported
        :param channel: the channel name
        :return: True if the channel is not unsupported, not ignored
        and if it's an authenticated channel if the exchange is authenticated
        """
        if self.cryptofeed_exchange.is_authenticated_channel(channel) and not self._should_use_authenticated_feeds():
            return False
        return channel != Feeds.UNSUPPORTED.value \
               and not self.should_ignore_feed(self.CRYPTOFEED_FEEDS_TO_WEBSOCKET_FEEDS[channel])

    def _subscribe_candle_feed(self):
        """
        Subscribes a new candle feed for each time frame
        """
        for time_frame in self.time_frames:
            self.client.add_feed(self.get_feed_name(),
                                 candle_interval=time_frame.value,
                                 symbols=self.filtered_pairs,
                                 log_message_on_error=True,
                                 channels=self.CANDLE_CHANNELS,
                                 callbacks={cryptofeed_constants.CANDLES: self.candle_callback})
            self.logger.debug(
                f"Subscribed to the {time_frame.value} time frame OHLCV for {', '.join(self.filtered_pairs)}")

    def _subscribe_pairs_feeds(self):
        """
        Subscribes all time frame unrelated feeds
        """
        self._subscribe_traded_pairs_feed()
        self._subscribe_watched_pairs_feed()

    def _subscribe_traded_pairs_feed(self):
        """
        Subscribes all time frame unrelated feeds for traded pairs
        """
        if self.channels:
            self.client.add_feed(self.get_feed_name(),
                                 symbols=self.filtered_pairs,
                                 log_message_on_error=True,
                                 channels=self.channels,
                                 callbacks=self.callbacks)
            for channel in self.channels:
                self.logger.debug(f"Subscribed to {channel} for {', '.join(self.filtered_pairs)}")

    def _subscribe_watched_pairs_feed(self):
        """
        Subscribes all time frame unrelated feeds for watched pairs
        """
        channels = [channel
                    for channel in self.WATCHED_PAIR_CHANNELS
                    if self._is_supported_channel(channel) and (channel in self.channels or not self.channels)]
        if self.watched_pairs and channels:
            self.client.add_feed(self.get_feed_name(),
                                 symbols=self.watched_pairs,
                                 log_message_on_error=True,
                                 channels=channels,
                                 callbacks=self.callbacks)
            for channel in channels:
                self.logger.debug(f"Subscribed to {channel} for {', '.join(self.watched_pairs)}")

    def _filter_exchange_pairs_and_timeframes(self):
        """
        Populates self.filtered_pairs and self.filtered_timeframes
        """
        self._filter_exchange_symbols()
        self._filter_exchange_time_frames()

    def _add_pair(self, pair, watching_only):
        """
        Add a pair to self.filtered_pairs if supported
        :param pair: the pair to add
        :param watching_only: when True add pair to watched_pairs else to filtered_pairs
        """
        if self._is_supported_pair(pair):
            if watching_only:
                self.watched_pairs.append(pair)
            else:
                self.filtered_pairs.append(pair)
        else:
            self.logger.error(f"{self.get_pair_from_exchange(pair)} pair is not supported by this exchange's websocket")

    def _filter_exchange_symbols(self):
        """
        Populates self.filtered_pairs from self.pairs when pair is supported by the cryptofeed exchange
        """
        for pair in self.pairs:
            self._add_pair(pair, watching_only=False)

    def _add_time_frame(self, time_frame):
        """
        Add a time frame to self.filtered_timeframes if supported
        :param time_frame: the time frame to add
        """
        try:
            if time_frame.value in self.cryptofeed_exchange.valid_candle_intervals:
                self.filtered_timeframes.append(time_frame)
            else:
                self.logger.error(f"{time_frame.value} time frame is not supported by this exchange's websocket")
        except AttributeError:
            # exchange.valid_candle_intervals is not implemented in each cryptofeed exchange
            pass

    def _filter_exchange_time_frames(self):
        """
        Populates self.filtered_timeframes from self.time_frames when time frame is supported by the cryptofeed exchange
        """
        for time_frame in self.time_frames:
            self._add_time_frame(time_frame)
        self.min_timeframe = time_frame_manager.find_min_time_frame(self.filtered_timeframes)

    def _should_run_candle_feed(self):
        return self.EXCHANGE_FEEDS.get(Feeds.CANDLE) and self.EXCHANGE_FEEDS.get(
            Feeds.CANDLE) != Feeds.UNSUPPORTED.value

    def _is_supported_pair(self, pair):
        return pair in self.cryptofeed_exchange.normalized_symbol_mapping

    def _is_supported_time_frame(self, time_frame):
        return time_frame.value in self.cryptofeed_exchange.valid_candle_intervals

    def _convert_book_prices_to_orders(self, book_prices, book_side):
        """
        Convert a book_prices format : {PRICE_1: SIZE_1, PRICE_2: SIZE_2...}
        to OctoBot's order book format
        :param book_prices: an order book dictionary
        :param book_side: a TradeOrderSide value
        :return: the list of order book data converted
        """
        return [
            {
                ECOBIC.PRICE.value: float(order_price),
                ECOBIC.SIZE.value: float(order_size),
                ECOBIC.SIDE.value: book_side,
            }
            for order_price, order_size in book_prices.items()
        ]

    def _set_async_callbacks(self):
        """
        Prevent `inspect.iscoroutinefunction` to return False when callback are cythonized
        """
        for callback in self.callback_by_feed.values():
            callback.is_async = True

    def _remove_all_feeds(self):
        """
        Call remove_feed for each client feeds
        """
        for feed in self.client.feeds:
            self._remove_feed(feed)

    def _remove_feed(self, feed):
        """
        Stops and removes a feed from running feeds
        :param feed: the feed instance to remove
        """
        try:
            feed.stop()
            self.client.feeds.remove(feed)
        except ValueError as ve:
            self.logger.error(f"Failed to remove feed from the list of feed : {ve}")
        except Exception as e:
            self.logger.error(f"Failed remove feed : {e}")

    def _fix_signal_handler(self):
        """
        Websocket are started in a new thread thus signal handle cannot be used
        add_signal_handler() can only be called from the main thread
        """
        cryptofeed.feedhandler.SIGNALS = ()

    def _fix_logger(self):
        """
        Replace cryptofeed feedhandler logger because it writes logs into "cryptofeed.log" file
        """
        cryptofeed.feedhandler.LOG = self.client_logger
        cryptofeed.connection_handler.LOG = self.client_logger

    """
    Callbacks
    """

    async def ticker(self, feed, symbol, bid, ask, timestamp, receipt_timestamp):
        if symbol:
            symbol = self.get_pair_from_exchange(symbol)
            # Can't create a full ticker from bid, ask, timestamp and symbol data
            # Push (ask + bid) / 2 as close price in MARK_PRICE channel
            await self.push_to_channel(channel_name=trading_constants.MARK_PRICE_CHANNEL,
                                       symbol=symbol,
                                       mark_price=float((ask + bid) / 2),
                                       mark_price_source=trading_enums.MarkPriceSources.TICKER_CLOSE_PRICE.value)

    async def trades(self, feed, symbol, order_id, timestamp, side, amount, price, receipt_timestamp):
        if symbol:
            symbol = self.get_pair_from_exchange(symbol)
            await self.push_to_channel(trading_constants.RECENT_TRADES_CHANNEL,
                                       symbol=symbol,
                                       recent_trades=[{
                                           trading_enums.ExchangeConstantsOrderColumns.TIMESTAMP.value: timestamp,
                                           trading_enums.ExchangeConstantsOrderColumns.SYMBOL.value: symbol,
                                           trading_enums.ExchangeConstantsOrderColumns.ID.value: order_id,
                                           trading_enums.ExchangeConstantsOrderColumns.TYPE.value: None,
                                           trading_enums.ExchangeConstantsOrderColumns.SIDE.value: side,
                                           trading_enums.ExchangeConstantsOrderColumns.PRICE.value: float(price),
                                           trading_enums.ExchangeConstantsOrderColumns.AMOUNT.value: float(amount)
                                       }])

    async def book(self, feed, symbol, book, timestamp, receipt_timestamp):
        if symbol:
            symbol = self.get_pair_from_exchange(symbol)
            book_instance = self.get_book_instance(symbol)

            book_instance.handle_book_adds(
                self._convert_book_prices_to_orders(
                    book_prices=book[cryptofeed_constants.ASK],
                    book_side=trading_enums.TradeOrderSide.SELL.value) +
                self._convert_book_prices_to_orders(
                    book_prices=book[cryptofeed_constants.BID],
                    book_side=trading_enums.TradeOrderSide.BUY.value))

            await self.push_to_channel(trading_constants.ORDER_BOOK_CHANNEL,
                                       symbol=symbol,
                                       asks=book_instance.asks,
                                       bids=book_instance.bids,
                                       update_order_book=False)

    async def candle(self, feed, symbol, start, stop, interval, trades, open_price, close_price, high_price,
                     low_price, volume, closed, timestamp, receipt_timestamp):
        if symbol:
            origin_symbol = symbol
            symbol = self.get_pair_from_exchange(symbol)
            time_frame = commons_enums.TimeFrames(interval)
            candle = [
                start,
                float(open_price),
                float(high_price),
                float(low_price),
                float(close_price),
                float(volume),
            ]
            ticker = {
                Ectc.HIGH.value: float(high_price),
                Ectc.LOW.value: float(low_price),
                Ectc.BID.value: None,
                Ectc.BID_VOLUME.value: None,
                Ectc.ASK.value: None,
                Ectc.ASK_VOLUME.value: None,
                Ectc.OPEN.value: float(open_price),
                Ectc.CLOSE.value: float(close_price),
                Ectc.LAST.value: float(close_price),
                Ectc.PREVIOUS_CLOSE.value: None,
                Ectc.BASE_VOLUME.value: float(volume),
                Ectc.TIMESTAMP.value: timestamp,
            }

            if origin_symbol not in self.watched_pairs:
                if not closed:
                    await self.push_to_channel(trading_constants.KLINE_CHANNEL,
                                               time_frame=time_frame,
                                               symbol=symbol,
                                               kline=candle)
                else:
                    await self.push_to_channel(trading_constants.OHLCV_CHANNEL,
                                               time_frame=time_frame,
                                               symbol=symbol,
                                               candle=candle)

            # Push a new ticker if necessary : only push on the min timeframe
            if time_frame is self.min_timeframe:
                await self.push_to_channel(trading_constants.TICKER_CHANNEL,
                                           symbol=symbol,
                                           ticker=ticker)

    async def delta(self, feed, symbol, delta, timestamp, receipt_timestamp):
        pass

    async def liquidations(self, feed, symbol, side, leaves_qty, price, order_id, receipt_timestamp):
        pass

    async def funding(self, **kwargs):
        pass

    async def open_interest(self, feed, symbol, open_interest, timestamp, receipt_timestamp):
        pass

    async def futures_index(self, **kwargs):
        pass

    async def order(self, feed, symbol, data, receipt_timestamp):
        """
        Cryptofeed order callback
        :param feed: the feed
        :param symbol: the order symbol
        :param data: a dict of miscellaneous data
        :param receipt_timestamp: received timestamp
        """
        await self.push_to_channel(trading_constants.ORDERS_CHANNEL, orders=[self.exchange.parse_order(data)])

    async def trade(self, feed, symbol, data, receipt_timestamp):
        """
        Cryptofeed filled order callback
        :param feed: the feed
        :param symbol: the filled order symbol
        :param data: a dict of miscellaneous data
        :param receipt_timestamp: received timestamp
        """
        await self.push_to_channel(trading_constants.TRADES_CHANNEL, trades=[self.exchange.parse_trade(data)])

    async def balance(self, feed, accounts):
        """
        Cryptofeed balance callback
        :param feed: the feed
        :param accounts: the balance dict
        """

    async def transaction(self, **kwargs):
        """
        Cryptofeed transaction callback
        """

    async def last_price(self, feed, symbol, last_price, receipt_timestamp):
        """
        Cryptofeed last price callback
        :param feed: the feed
        :param symbol: the last price symbol
        :param last_price: the last price
        :param receipt_timestamp: received timestamp
        """

    async def user_data(self, feed, data, receipt_timestamp):
        """
        Cryptofeed user data callback
        Entrypoint of order, trades, etc. updates
        Example : https://docs.deribit.com/#user-changes-instrument_name-interval
        :param feed: the feed
        :param data: received user data
        :param receipt_timestamp: received timestamp
        """
