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
import decimal
import logging
import os
import threading

import cryptofeed
import cryptofeed.callback as cryptofeed_callbacks
import cryptofeed.config as cryptofeed_config
import cryptofeed.connection_handler
import cryptofeed.defines as cryptofeed_constants
import cryptofeed.exchanges as cryptofeed_exchanges
import cryptofeed.types as cryptofeed_types

import octobot_commons
import octobot_commons.asyncio_tools as asyncio_tools
import octobot_commons.enums as commons_enums
import octobot_commons.logging as commons_logging
import octobot_commons.symbols as symbol_util
import octobot_commons.time_frame_manager as time_frame_manager

import octobot_trading.constants as trading_constants
import octobot_trading.enums as trading_enums
import octobot_trading.exchanges.abstract_websocket_exchange as abstract_websocket
import octobot_trading.exchanges.connectors.abstract_websocket_connector as abstract_websocket_connector
from octobot_trading.enums import ExchangeConstantsOrderBookInfoColumns as ECOBIC, \
    ExchangeConstantsTickersColumns as Ectc
from octobot_trading.enums import WebsocketFeeds as Feeds


class CryptofeedWebsocketConnector(abstract_websocket.AbstractWebsocketExchange):
    CRYPTOFEED_LOGGERS = ["feedhandler"] + abstract_websocket_connector.AbstractWebsocketConnector.LOGGERS
    CRYPTOFEED_DEFAULT_MARKET_SEPARATOR = "-"

    INIT_REQUIRING_EXCHANGE_FEEDS = [Feeds.CANDLE]

    IGNORED_FEED_PAIRS = {
        # When ticker or future index is available : no need to calculate mark price from recent trades
        Feeds.TRADES: [Feeds.TICKER, Feeds.FUTURES_INDEX],
        # When candles are available : use min timeframe kline to push ticker
        Feeds.TICKER: [Feeds.KLINE]
    }

    CRYPTOFEED_FEEDS_TO_WEBSOCKET_FEEDS = {
        # Unauthenticated
        cryptofeed_constants.TRADES: Feeds.TRADES,
        cryptofeed_constants.TICKER: Feeds.TICKER,
        cryptofeed_constants.CANDLES: Feeds.CANDLE,
        cryptofeed_constants.L1_BOOK: Feeds.L1_BOOK,
        cryptofeed_constants.L2_BOOK: Feeds.L2_BOOK,
        cryptofeed_constants.L3_BOOK: Feeds.L3_BOOK,
        cryptofeed_constants.FUNDING: Feeds.FUNDING,
        cryptofeed_constants.LIQUIDATIONS: Feeds.LIQUIDATIONS,
        cryptofeed_constants.OPEN_INTEREST: Feeds.OPEN_INTEREST,
        cryptofeed_constants.INDEX: Feeds.FUTURES_INDEX,

        # Authenticated
        cryptofeed_constants.TRANSACTIONS: Feeds.TRANSACTIONS,
        cryptofeed_constants.BALANCES: Feeds.PORTFOLIO,
        cryptofeed_constants.PLACE_ORDER: Feeds.ORDERS,
        cryptofeed_constants.CANCEL_ORDER: Feeds.ORDERS,
        cryptofeed_constants.ORDERS: Feeds.ORDERS,
        cryptofeed_constants.ORDER_STATUS: Feeds.ORDERS,
        cryptofeed_constants.ORDER_INFO: Feeds.ORDERS,
        cryptofeed_constants.TRADE_HISTORY: Feeds.TRADE,
        cryptofeed_constants.FILLS: Feeds.TRADE,
        cryptofeed_constants.POSITIONS: Feeds.POSITION,
    }

    PAIR_INDEPENDENT_CHANNELS = [
        cryptofeed_constants.BALANCES,
        cryptofeed_constants.ORDER_INFO,
    ]
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
            # Unauthenticated
            cryptofeed_constants.TRADES: cryptofeed_callbacks.TradeCallback(self.trades),
            cryptofeed_constants.TICKER: cryptofeed_callbacks.TickerCallback(self.ticker),
            cryptofeed_constants.CANDLES: cryptofeed_callbacks.CandleCallback(self.candle),
            cryptofeed_constants.FUNDING: cryptofeed_callbacks.FundingCallback(self.funding),
            cryptofeed_constants.OPEN_INTEREST: cryptofeed_callbacks.OpenInterestCallback(self.open_interest),
            cryptofeed_constants.LIQUIDATIONS: cryptofeed_callbacks.LiquidationCallback(self.liquidations),
            cryptofeed_constants.INDEX: cryptofeed_callbacks.IndexCallback(self.index),
            cryptofeed_constants.L2_BOOK: cryptofeed_callbacks.BookCallback(self.book),

            # Authenticated
            cryptofeed_constants.ORDER_INFO: cryptofeed_callbacks.OrderInfoCallback(self.order),
            cryptofeed_constants.TRANSACTIONS: cryptofeed_callbacks.TransactionsCallback(self.transaction),
            cryptofeed_constants.BALANCES: cryptofeed_callbacks.BalancesCallback(self.balance),
            cryptofeed_constants.FILLS: cryptofeed_callbacks.UserFillsCallback(self.fill),
        }
        self._set_async_callbacks()

        # Create cryptofeed FeedHandler instance
        self._create_client()

        # Creates cryptofeed exchange instance
        self.cryptofeed_exchange = cryptofeed_exchanges.EXCHANGE_MAP[self.get_feed_name()](
            config=self.client_config,
            **self._get_feed_default_kwargs()
        )

        self._previous_open_candles = {}
        self._full_symbol_by_feed_symbol = {}

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
            self._subscribe_channels_feeds()
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

    def get_cryptofeed_symbol(self, symbol):
        return symbol

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
            return self._get_full_symbol(
                symbol_util.convert_symbol(
                    symbol=pair,
                    symbol_separator=self.CRYPTOFEED_DEFAULT_MARKET_SEPARATOR,
                    new_symbol_separator=octobot_commons.MARKET_SEPARATOR,
                    should_uppercase=True,
                )
            )
        except Exception:
            self.logger.error(f"Failed to get market of {pair}")
        return ""

    def _get_full_symbol(self, feed_symbol):
        try:
            return self._full_symbol_by_feed_symbol[feed_symbol]
        except KeyError:
            return feed_symbol

    def get_exchange_pair(self, pair) -> str:
        """
        Convert an uniformized symbol format to a cryptofeed symbol format
        :param pair: the pair to format
        :return: the cryptofeed pair when success else an empty string
        """
        try:
            feed_symbol = symbol_util.convert_symbol(
                symbol=pair,
                symbol_separator=octobot_commons.MARKET_SEPARATOR,
                new_symbol_separator=self.CRYPTOFEED_DEFAULT_MARKET_SEPARATOR,
                should_uppercase=True,
                base_and_quote_only=True,
            )
            self._full_symbol_by_feed_symbol[feed_symbol] = pair
            return feed_symbol
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
            if self.min_timeframe is None:
                self.logger.error(
                    f"Missing min_timeframe in exchange websocket with candle feeds. This probably means that no "
                    f"required time frame is supported by this exchange's websocket "
                    f"(valid_candle_intervals: {self.cryptofeed_exchange.valid_candle_intervals})")
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
        try:
            self.callbacks[self.EXCHANGE_FEEDS[Feeds.CANDLE]] = self.candle_callback
        except KeyError:
            pass  # ignore candle callback when Candles feed is not supported

        self._subscribe_channels_feeds()

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
            try:
                self._subscribe_feed(
                    symbols=self.filtered_pairs,
                    candle_interval=time_frame.value,
                    channels=self.CANDLE_CHANNELS,
                    callbacks={cryptofeed_constants.CANDLES: self.candle_callback}
                )
            except ValueError as e:
                self.logger.exception(e, True,
                                      f"Error when subscribing to feed: ignored candle feed with {self.filtered_pairs} "
                                      f"on {time_frame.value} ({e})")

    def _subscribe_channels_feeds(self):
        """
        Subscribes all time frame unrelated feeds
        """
        self._subscribe_pair_independent_feed()
        self._subscribe_traded_pairs_feed()
        self._subscribe_watched_pairs_feed()

    def _subscribe_pair_independent_feed(self):
        """
        Subscribes all pair unrelated feeds
        """
        channels = [channel for channel in self.channels if self._is_pair_independent_feed(channel)]
        if channels:
            self._subscribe_feed(
                channels=channels,
                callbacks=self.callbacks
            )

    def _subscribe_traded_pairs_feed(self):
        """
        Subscribes all time frame unrelated feeds for traded pairs
        """
        channels = [channel for channel in self.channels if not self._is_pair_independent_feed(channel)]
        if channels:
            self._subscribe_feed(
                symbols=self.filtered_pairs,
                channels=channels,
                callbacks=self.callbacks
            )

    def _subscribe_watched_pairs_feed(self):
        """
        Subscribes feeds for watched pairs (only on one timeframe for multiple timeframes feeds)
        """
        channels = [channel
                    for channel in self.WATCHED_PAIR_CHANNELS
                    if self._is_supported_channel(channel) and (channel in self.channels or not self.channels)]
        if self.watched_pairs and channels:
            self._subscribe_feed(
                symbols=self.watched_pairs,
                channels=channels,
                callbacks=self.callbacks
            )

    def _get_feed_default_kwargs(self):
        kwargs = {
            "candle_closed_only": False,
            "sandbox": self.exchange_manager.is_sandboxed
        }
        # apply exchange kwargs
        kwargs.update(self.EXCHANGE_CONSTRUCTOR_KWARGS)
        return kwargs

    def _subscribe_feed(self, channels, callbacks, symbols=None, candle_interval=None):
        """
        Subscribe a new feed
        :param symbols: the feed symbols
        :param candle_interval: the feed candle_interval
        :param channels: the feed channels
        :param callbacks: the feed callbacks
        """
        feed_kwargs = self._get_feed_default_kwargs()
        if symbols:
            feed_kwargs["symbols"] = symbols
        if candle_interval:
            # always specify candle_interval even if not always used
            feed_kwargs["candle_interval"] = candle_interval or \
                                             self.min_timeframe.value if self.min_timeframe else candle_interval
        self.client.add_feed(self.get_feed_name(),
                             log_message_on_error=True,
                             callbacks=callbacks,
                             channels=channels,
                             **feed_kwargs)
        for channel in channels:
            symbols_str = f"for {', '.join(symbols)} " if symbols else ""
            candle_interval_str = f"on {candle_interval}" if candle_interval else ""
            self.logger.debug(f"Subscribed to {channel} {symbols_str}{candle_interval_str}")

    def _filter_exchange_pairs_and_timeframes(self):
        """
        Populates self.filtered_pairs and self.min_timeframe
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

    def _add_time_frame(self, filtered_timeframes, time_frame, log_on_error):
        """
        Add a time frame to filtered_timeframes if supported
        :param time_frame: the time frame to add
        """
        try:
            if self.cryptofeed_exchange.valid_candle_intervals is not NotImplemented and \
                    time_frame.value in self.cryptofeed_exchange.valid_candle_intervals :
                filtered_timeframes.append(time_frame)
            elif log_on_error:
                self.logger.error(f"{time_frame.value} time frame is not supported by this exchange's websocket")
        except AttributeError:
            # exchange.valid_candle_intervals is not implemented in each cryptofeed exchange
            pass

    def _filter_exchange_time_frames(self):
        """
        Populates self.min_timeframe from self.time_frames when time frame is supported by the cryptofeed exchange
        Leaves self.min_timeframe at None if no timeframe is available on this exchange ws
        """
        # Log error only if necessary (self.min_timeframe is used by candle feed only)
        log_on_error = self._should_run_candle_feed()
        filtered_timeframes = []
        for time_frame in self.time_frames:
            self._add_time_frame(filtered_timeframes, time_frame, log_on_error)
        if filtered_timeframes:
            self.min_timeframe = time_frame_manager.find_min_time_frame(filtered_timeframes)

    def _should_run_candle_feed(self):
        return self.EXCHANGE_FEEDS.get(Feeds.CANDLE) and self.EXCHANGE_FEEDS.get(
            Feeds.CANDLE) != Feeds.UNSUPPORTED.value

    def _is_supported_pair(self, pair):
        return pair in self.cryptofeed_exchange.normalized_symbol_mapping

    def _is_supported_time_frame(self, time_frame):
        return time_frame.value in self.cryptofeed_exchange.valid_candle_intervals

    def _is_pair_independent_feed(self, feed):
        return feed in self.PAIR_INDEPENDENT_CHANNELS

    def _convert_book_prices_to_orders(self, book_prices, book_side):
        """
        Convert a book_prices format : {PRICE_1: SIZE_1, PRICE_2: SIZE_2...}
        to OctoBot's order book format
        :param book_prices: an order book dictionary (order_book.SortedDict)
        :param book_side: a TradeOrderSide value
        :return: the list of order book data converted
        """
        return [
            {
                ECOBIC.PRICE.value: float(order_price),
                ECOBIC.SIZE.value: float(order_size),
                ECOBIC.SIDE.value: book_side,
            }
            for order_price, order_size in book_prices.to_dict().items()
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

    async def ticker(self, ticker: cryptofeed_types.Ticker, receipt_timestamp: float):
        """
        Cryptofeed ticker callback
        :param ticker: the ticker object defined in cryptofeed.types.Ticker
        :param receipt_timestamp: received timestamp
        """
        symbol = self.get_pair_from_exchange(ticker.symbol)
        # Can't create a full ticker from bid, ask, timestamp and symbol data
        # Push (ask + bid) / 2 as close price in MARK_PRICE channel
        await self.push_to_channel(trading_constants.MARK_PRICE_CHANNEL,
                                   symbol,
                                   (ticker.ask + ticker.bid) / decimal.Decimal(2),
                                   mark_price_source=trading_enums.MarkPriceSources.TICKER_CLOSE_PRICE.value)

    async def trades(self, trade: cryptofeed_types.Trade, receipt_timestamp: float):
        """
        Cryptofeed ticker callback
        :param trade: the trade object defined in cryptofeed.types.Trade
        :param receipt_timestamp: received timestamp
        """
        symbol = self.get_pair_from_exchange(trade.symbol)
        await self.push_to_channel(trading_constants.RECENT_TRADES_CHANNEL,
                                   symbol,
                                   [{
                                       trading_enums.ExchangeConstantsOrderColumns.TIMESTAMP.value: trade.timestamp,
                                       trading_enums.ExchangeConstantsOrderColumns.SYMBOL.value: symbol,
                                       trading_enums.ExchangeConstantsOrderColumns.ID.value: trade.id,
                                       trading_enums.ExchangeConstantsOrderColumns.TYPE.value: None,
                                       trading_enums.ExchangeConstantsOrderColumns.SIDE.value: trade.side,
                                       trading_enums.ExchangeConstantsOrderColumns.PRICE.value: float(trade.price),
                                       trading_enums.ExchangeConstantsOrderColumns.AMOUNT.value: float(trade.amount)
                                   }])

    async def book(self, order_book: cryptofeed_types.OrderBook, receipt_timestamp: float):
        """
        Cryptofeed orderbook callback
        :param order_book: the order_book object defined in cryptofeed.types.OrderBook
        :param receipt_timestamp: received timestamp
        """
        symbol = self.get_pair_from_exchange(order_book.symbol)
        book_instance = self.get_book_instance(symbol)

        book_instance.handle_book_adds(
            self._convert_book_prices_to_orders(
                book_prices=order_book.book.asks,
                book_side=trading_enums.TradeOrderSide.SELL.value) +
            self._convert_book_prices_to_orders(
                book_prices=order_book.book.bids,
                book_side=trading_enums.TradeOrderSide.BUY.value))

        await self.push_to_channel(trading_constants.ORDER_BOOK_CHANNEL,
                                   symbol,
                                   book_instance.asks,
                                   book_instance.bids,
                                   update_order_book=False)

    async def candle(self, candle_data: cryptofeed_types.Candle, receipt_timestamp: float):
        """
        Cryptofeed candle callback
        :param candle_data: the candle object defined in cryptofeed.types.Candle
        :param receipt_timestamp: received timestamp
        """
        symbol = self.get_pair_from_exchange(candle_data.symbol)
        time_frame = commons_enums.TimeFrames(candle_data.interval)
        candle = [
            candle_data.start,
            float(candle_data.open),
            float(candle_data.high),
            float(candle_data.low),
            float(candle_data.close),
            float(candle_data.volume),
        ]
        ticker = {
            Ectc.HIGH.value: float(candle_data.high),
            Ectc.LOW.value: float(candle_data.low),
            Ectc.BID.value: None,
            Ectc.BID_VOLUME.value: None,
            Ectc.ASK.value: None,
            Ectc.ASK_VOLUME.value: None,
            Ectc.OPEN.value: float(candle_data.open),
            Ectc.CLOSE.value: float(candle_data.close),
            Ectc.LAST.value: float(candle_data.close),
            Ectc.PREVIOUS_CLOSE.value: None,
            Ectc.BASE_VOLUME.value: float(candle_data.volume),
            Ectc.TIMESTAMP.value: self.exchange.get_exchange_current_time(),
        }

        if candle_data.symbol not in self.watched_pairs:
            previous_candle = self._get_previous_open_candle(time_frame, symbol)
            push_previous_candle = previous_candle is not None and \
                previous_candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value] < candle_data.start
            if candle_data.closed or push_previous_candle:
                if candle_data.closed and previous_candle is not None and \
                   previous_candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value] > candle_data.start:
                    self.logger.warning(f"Duplicate closed candle: pushing already pushed closed "
                                        f"candle: [{candle_data}]")
                await self.push_to_channel(trading_constants.OHLCV_CHANNEL,
                                           time_frame,
                                           symbol,
                                           previous_candle if push_previous_candle else candle)
                # closed candle has been fetched from exchange, use it and reset previous open candle
                self._register_previous_open_candle(time_frame, symbol, None)
            if not candle_data.closed:
                await self.push_to_channel(trading_constants.KLINE_CHANNEL,
                                           time_frame,
                                           symbol,
                                           candle)
                self._register_previous_open_candle(time_frame, symbol, candle)

        # Push a new ticker if necessary : only push on the min timeframe
        if time_frame is self.min_timeframe:
            await self.push_to_channel(trading_constants.TICKER_CHANNEL,
                                       symbol,
                                       ticker)

    async def liquidations(self, liquidation: cryptofeed_types.Liquidation, receipt_timestamp: float):
        """
        Cryptofeed liquidation callback
        :param liquidation: the liquidation object defined in cryptofeed.types.Liquidation
        :param receipt_timestamp: received timestamp
        """

    async def funding(self, funding: cryptofeed_types.Funding, receipt_timestamp: float):
        """
        Cryptofeed funding callback
        :param funding: the funding object defined in cryptofeed.types.Funding
        :param receipt_timestamp: received timestamp
        """
        symbol = self.get_pair_from_exchange(funding.symbol)
        await self.push_to_channel(trading_constants.FUNDING_CHANNEL,
                                   symbol,
                                   funding.rate,
                                   funding.predicted_rate,
                                   funding.next_funding_time,
                                   funding.timestamp)
        await self.push_to_channel(trading_constants.MARK_PRICE_CHANNEL,
                                   symbol,
                                   funding.mark_price)

    async def open_interest(self, open_interest: cryptofeed_types.OpenInterest, receipt_timestamp: float):
        """
        Cryptofeed open interest callback
        :param open_interest: the open_interest object defined in cryptofeed.types.OpenInterest
        :param receipt_timestamp: received timestamp
        """

    async def index(self, index: cryptofeed_types.Index, receipt_timestamp: float):
        """
        Cryptofeed future index callback
        :param index: the index object defined in cryptofeed.types.Index
        :param receipt_timestamp: received timestamp
        """
        await self.push_to_channel(trading_constants.MARK_PRICE_CHANNEL,
                                   self.get_pair_from_exchange(index.symbol),
                                   index.price,
                                   trading_enums.MarkPriceSources.EXCHANGE_MARK_PRICE.value)

    async def order(self, order: cryptofeed_types.OrderInfo, receipt_timestamp: float):
        """
        Cryptofeed order callback
        :param order the order object defined in cryptofeed.types.?
        :param receipt_timestamp: received timestamp
        """
        await self.push_to_channel(trading_constants.ORDERS_CHANNEL, [{
            trading_enums.ExchangeConstantsOrderColumns.TYPE.value: self._parse_order_type(order.type),
            trading_enums.ExchangeConstantsOrderColumns.STATUS.value: self._parse_order_status(order.status),
            trading_enums.ExchangeConstantsOrderColumns.ID.value: order.id,
            trading_enums.ExchangeConstantsOrderColumns.SYMBOL.value: order.symbol,
            trading_enums.ExchangeConstantsOrderColumns.PRICE.value: order.price,
            trading_enums.ExchangeConstantsOrderColumns.AMOUNT.value: order.amount,
            trading_enums.ExchangeConstantsOrderColumns.REMAINING.value: order.remaining,
            trading_enums.ExchangeConstantsOrderColumns.FILLED.value: order.amount - order.remaining,
            trading_enums.ExchangeConstantsOrderColumns.TIMESTAMP.value: order.timestamp,
            trading_enums.ExchangeConstantsOrderColumns.SIDE.value: self._parse_order_side(order.side)
        }])

    async def trade(self, trade, receipt_timestamp: float):
        """
        Cryptofeed filled order callback
        :param trade: the trade object defined in cryptofeed.types.?
        :param receipt_timestamp: received timestamp
        """
        await self.push_to_channel(trading_constants.TRADES_CHANNEL, [self.exchange.parse_trade(trade)])

    async def balance(self, balance: cryptofeed_types.Balance, receipt_timestamp: float):
        """
        Cryptofeed balance callback
        :param balance: the balance object defined in cryptofeed.types.Balance
        :param receipt_timestamp: received timestamp
        """
        await self.push_to_channel(trading_constants.BALANCE_CHANNEL,
                                   self.exchange.parse_balance(balance.balance))

    async def transaction(self, transaction: cryptofeed_types.Transaction, receipt_timestamp: float):
        """
        Cryptofeed transaction callback
        :param transaction: the transaction object defined in cryptofeed.types.Transaction
        :param receipt_timestamp: received timestamp
        """

    async def fill(self, fill: cryptofeed_types.Fill, receipt_timestamp: float):
        """
        Cryptofeed fill callback
        :param fill: the fill object defined in cryptofeed.types.Fill
        :param receipt_timestamp: received timestamp
        """

    """
    Parsers
    """

    def _parse_order_type(self, raw_order_type):
        """
        :param raw_order_type: the cryptofeed unified order type
        :return: the unified OctoBot order type
        """
        # TODO Migrate to switch case with python 3.10
        if raw_order_type == cryptofeed_constants.LIMIT:
            return trading_enums.TradeOrderType.LIMIT.value
        elif raw_order_type == cryptofeed_constants.MARKET:
            return trading_enums.TradeOrderType.MARKET.value
        elif raw_order_type == cryptofeed_constants.STOP_LIMIT:
            return trading_enums.TradeOrderType.STOP_LOSS_LIMIT.value
        elif raw_order_type == cryptofeed_constants.STOP_MARKET:
            return trading_enums.TradeOrderType.STOP_LOSS.value
        elif raw_order_type == cryptofeed_constants.MAKER_OR_CANCEL:
            pass
        elif raw_order_type == cryptofeed_constants.FILL_OR_KILL:
            pass
        elif raw_order_type == cryptofeed_constants.IMMEDIATE_OR_CANCEL:
            pass
        elif raw_order_type == cryptofeed_constants.GOOD_TIL_CANCELED:
            pass
        self.logger.error(f"Failed to parse {raw_order_type} order type (not supported).")
        return None

    def _parse_order_status(self, raw_order_status):
        """
        :param raw_order_status: the cryptofeed unified order status
        :return: the unified OctoBot order status
        """
        # TODO Migrate to switch case with python 3.10
        if raw_order_status == cryptofeed_constants.OPEN:
            return trading_enums.OrderStatus.OPEN.value
        elif raw_order_status == cryptofeed_constants.PENDING:
            return trading_enums.OrderStatus.OPEN.value
        elif raw_order_status == cryptofeed_constants.FILLED:
            return trading_enums.OrderStatus.FILLED.value
        elif raw_order_status == cryptofeed_constants.PARTIAL:
            return trading_enums.OrderStatus.PARTIALLY_FILLED.value
        elif raw_order_status == cryptofeed_constants.CANCELLED:
            return trading_enums.OrderStatus.CANCELED.value
        elif raw_order_status == cryptofeed_constants.UNFILLED:
            return trading_enums.OrderStatus.OPEN.value
        elif raw_order_status == cryptofeed_constants.EXPIRED:
            return trading_enums.OrderStatus.EXPIRED.value
        elif raw_order_status == cryptofeed_constants.FAILED:
            return trading_enums.OrderStatus.REJECTED.value
        elif raw_order_status == cryptofeed_constants.SUBMITTING:
            return trading_enums.OrderStatus.OPEN.value
        elif raw_order_status == cryptofeed_constants.CANCELLING:
            return trading_enums.OrderStatus.PENDING_CANCEL.value
        elif raw_order_status == cryptofeed_constants.CLOSED:
            return trading_enums.OrderStatus.CLOSED.value
        elif raw_order_status == cryptofeed_constants.SUSPENDED:
            pass
        self.logger.error(f"Failed to parse {raw_order_status} order status (not supported).")
        return None

    def _parse_order_side(self, raw_order_side):
        """
        :param raw_order_side: the cryptofeed unified order side
        :return: the unified OctoBot order side
        """
        return trading_enums.TradeOrderSide.BUY.value \
            if raw_order_side == cryptofeed_constants.BUY else trading_enums.TradeOrderSide.SELL.value

    def _register_previous_open_candle(self, time_frame, symbol, candle):
        try:
            self._previous_open_candles[time_frame][symbol] = candle
        except KeyError:
            if time_frame not in self._previous_open_candles:
                self._previous_open_candles[time_frame] = {}
            self._previous_open_candles[time_frame][symbol] = candle

    def _get_previous_open_candle(self, time_frame, symbol):
        try:
            return self._previous_open_candles[time_frame][symbol]
        except KeyError:
            return None
