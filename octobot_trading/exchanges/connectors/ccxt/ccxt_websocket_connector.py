# pylint: disable=W0101
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
import copy
import decimal
import time

import ccxt
import ccxt.pro as ccxtpro

import octobot_commons.asyncio_tools as asyncio_tools
import octobot_commons.enums as commons_enums
import octobot_commons.constants as commons_constants
import octobot_commons.time_frame_manager as time_frame_manager

import octobot_trading.constants as trading_constants
import octobot_trading.enums as trading_enums
import octobot_trading.exchanges.abstract_websocket_exchange as abstract_websocket_exchange
import octobot_trading.exchanges.connectors.ccxt.ccxt_client_util as ccxt_client_util
import octobot_trading.exchanges.connectors.ccxt.ccxt_adapter as ccxt_adapter
from octobot_trading.enums import ExchangeConstantsOrderBookInfoColumns as ECOBIC, \
    ExchangeConstantsTickersColumns as Ectc
from octobot_trading.enums import WebsocketFeeds as Feeds


class CCXTWebsocketConnector(abstract_websocket_exchange.AbstractWebsocketExchange):
    INIT_REQUIRING_EXCHANGE_FEEDS = [Feeds.CANDLE]
    SUPPORTS_LIVE_PAIR_ADDITION = True
    FEED_INITIALIZATION_TIMEOUT = 15 * commons_constants.MINUTE_TO_SECONDS

    IGNORED_FEED_PAIRS = {
        # When ticker or future index is available : no need to calculate mark price from recent trades
        Feeds.TRADES: [Feeds.TICKER, Feeds.FUTURES_INDEX],
        # When candles are available : use min timeframe kline to push ticker
        Feeds.TICKER: [Feeds.KLINE]
    }

    PAIR_INDEPENDENT_CHANNELS = [
        Feeds.PORTFOLIO,
        Feeds.ORDERS,
        Feeds.CREATE_ORDER,
        Feeds.CANCEL_ORDER,
        Feeds.TRADE,
        Feeds.LEDGER,
        Feeds.PORTFOLIO,
    ]
    WATCHED_PAIR_CHANNELS = [
        Feeds.TRADES,
        Feeds.TICKER,
        Feeds.CANDLE,
    ]
    TIME_FRAME_PAIR_CHANNELS = [
        Feeds.CANDLE,
        Feeds.KLINE,
    ]
    CURRENT_TIME_FILTERED_CHANNELS = [
        Feeds.TRADES,
        Feeds.ORDERS,
        Feeds.TRADE,
    ]
    CANDLE_TIME_FILTERED_CHANNELS = [
        Feeds.CANDLE,
        Feeds.KLINE,
    ]
    # https://docs.ccxt.com/en/latest/ccxt.pro.manual.html?rtd_search=fetchLedger#real-time-vs-throttling
    # THROTTLED_CHANNELS are updated at each self.throttled_ws_updates.
    # Used as real time channels when self.throttled_ws_updates is 0
    # self.throttled_ws_updates is using trading_constants.THROTTLED_WS_UPDATES by default
    THROTTLED_CHANNELS = [
        Feeds.TICKER,
        Feeds.TRADES,
        Feeds.L1_BOOK,
        Feeds.L2_BOOK,
        Feeds.L3_BOOK,
    ]
    AUTHENTICATED_CHANNELS = [
        trading_enums.WebsocketFeeds.ORDERS,
        trading_enums.WebsocketFeeds.PORTFOLIO,
        trading_enums.WebsocketFeeds.TRADE,
        trading_enums.WebsocketFeeds.POSITION,
    ]
    EXCHANGE_CONSTRUCTOR_KWARGS = {}
    RECONNECT_DELAY = 5

    def __init__(self, config, exchange_manager, adapter_class=None, additional_config=None):
        super().__init__(config, exchange_manager)
        self.filtered_pairs = []
        self.watched_pairs = []
        self.min_timeframe = None
        self._previous_open_candles = {}
        self._start_time_millis = None  # used for the "since" param in CURRENT/CANDLE_TIME_FILTERED_CHANNELS

        self.local_loop = None

        self.should_stop = False
        self.is_authenticated = False
        self.adapter = self.get_adapter_class(adapter_class)(self)
        self.additional_config = additional_config
        self.headers = {}
        self.options = {
            "newUpdates": True  # only get new updates from trades and ohlcv (don't return the full cached history)
        }
        # add default options
        self.add_options(
            ccxt_client_util.get_ccxt_client_login_options(self.exchange_manager)
        )
        self.client = None  # ccxt.pro exchange: a ccxt.async_support exchange with websocket capabilities
        self.feed_tasks = {}
        self.throttled_ws_updates = trading_constants.THROTTLED_WS_UPDATES

        self._create_client()

    """
    Methods
    """

    @classmethod
    def get_feed_name(cls):
        return cls.get_name()

    def start(self):
        asyncio.run(self._inner_start())

    async def _inner_start(self):
        self._start_time_millis = self.client.milliseconds()
        self.stopped_event = asyncio.Event()
        self.local_loop = asyncio.get_event_loop()
        await self._init_client()
        # keep loop open till stop is called
        await self.stopped_event.wait()

    def get_adapter_class(self, adapter_class):
        return adapter_class or ccxt_adapter.CCXTAdapter

    def add_headers(self, headers_dict):
        """
        Add new headers to ccxt client
        :param headers_dict: the additional header keys and values as dict
        """
        self.headers.update(headers_dict)
        if self.client is not None:
            ccxt_client_util.add_headers(self.client, headers_dict)

    def add_options(self, options_dict):
        """
        Add new options to ccxt client
        :param options_dict: the additional option keys and values as dict
        """
        self.options.update(options_dict)
        if self.client is not None:
            ccxt_client_util.add_options(self.client, options_dict)

    async def _inner_stop(self):
        self.should_stop = True
        try:
            await self.client.close()
            self.stopped_event.set()
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

    def add_pairs(self, pairs, watching_only=False):
        """
        Add new pairs to self.filtered_pairs
        :param pairs: the list of pair to add
        :param watching_only: if pairs are for watching or trading purpose
        """
        for pair in pairs:
            self._add_pair(pair, watching_only=watching_only)

    async def _inner_update_followed_pairs(self):
        if self.initialized_event is None:
            # should never happen
            return
        if not self.initialized_event.is_set():
            await self.initialized_event.wait()
        self._filter_exchange_symbols()
        self._subscribe_channels_feeds(True)

    def update_followed_pairs(self):
        asyncio_tools.run_coroutine_in_asyncio_loop(self._inner_update_followed_pairs(), self.local_loop)

    @classmethod
    def is_supporting_exchange(cls, exchange_candidate_name) -> bool:
        return cls.get_name() == exchange_candidate_name

    def get_pair_from_exchange(self, pair):
        """
        Convert a ccxt symbol format to uniformized symbol format
        :param pair: the pair to format
        :return: the formatted pair when success else an empty string
        """
        # octobot uses the ccxt format for pairs
        return pair

    def get_exchange_pair(self, pair) -> str:
        """
        Convert an uniformized symbol format to a ccxt symbol format
        :param pair: the pair to format
        :return: the ccxt pair when success else an empty string
        """
        # octobot uses the ccxt format for pairs
        return pair

    """
    Private methods
    """

    def _create_client(self):
        """
        Creates ccxt client instance
        """
        client_class = getattr(ccxtpro, self.get_feed_name())
        self.client, self.is_authenticated = ccxt_client_util.create_client(
            client_class, self.name, self.exchange_manager, self.logger,
            self.options, self.headers, self.additional_config,
            self._should_authenticate()
        )

    def _should_authenticate(self):
        return self._has_authenticated_channel() and super()._should_authenticate()

    def _has_authenticated_channel(self) -> bool:
        for feed in self.AUTHENTICATED_CHANNELS:
            if feed in self.EXCHANGE_FEEDS:
                return True
        return False

    def _is_authenticated_feed(self, feed):
        return feed in self.AUTHENTICATED_CHANNELS

    async def _init_client(self):
        """
        Prepares client configuration and instantiates client feeds
        """
        try:
            self.initialized_event = asyncio.Event()
            await self.client.load_markets()
            self._filter_exchange_pairs_and_timeframes()
            self._subscribe_feeds()
        except Exception as e:
            self.logger.exception(e, True, f"Failed to subscribe when creating websocket feed : {e}")
        finally:
            self.initialized_event.set()

    def _subscribe_feeds(self):
        """
        Prepares the subscription of unauthenticated and authenticated feeds and subscribe all
        """
        if self._should_run_candle_feed():
            if self.min_timeframe is None:
                self.logger.error(
                    f"Missing min_timeframe in exchange websocket with candle feeds. This probably means that no "
                    f"required time frame is supported by this exchange's websocket "
                    f"(valid_candle_intervals: {ccxt_client_util.get_time_frames(self.client)})")
            self._subscribe_candle_feed()

        # drop unsupported channels
        self.channels = [
            channel for channel in self.channels
            if self._is_supported_channel(channel)
            and channel != self.EXCHANGE_FEEDS.get(Feeds.CANDLE)
        ]

        self._subscribe_channels_feeds(False)

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
        if self._is_authenticated_feed(channel) and not self._should_use_authenticated_feeds():
            return False
        return not (
            self.EXCHANGE_FEEDS.get(channel, Feeds.UNSUPPORTED.value) == Feeds.UNSUPPORTED.value
            or self.should_ignore_feed(channel)
        )

    @classmethod
    def get_exchange_feed(cls, feed) -> str:
        feed_value = cls.EXCHANGE_FEEDS.get(feed, trading_enums.WebsocketFeeds.UNSUPPORTED.value)
        if cls.is_feed_supported(feed_value):
            return feed.value
        return trading_enums.WebsocketFeeds.UNSUPPORTED.value

    def _subscribe_candle_feed(self):
        """
        Subscribes a new candle feed for each time frame
        """
        for time_frame in self.time_frames:
            self._subscribe_feed(
                Feeds.CANDLE,
                symbols=self.filtered_pairs,
                time_frame=time_frame.value,
            )

    def _subscribe_channels_feeds(self, pairs_related_channels_only):
        """
        Subscribes all time frame unrelated feeds
        """
        if not pairs_related_channels_only:
            self._subscribe_pair_independent_feed()
        self._subscribe_traded_pairs_feed()
        self._subscribe_watched_pairs_feed()

    def _subscribe_pair_independent_feed(self):
        """
        Subscribes all pair unrelated feeds
        """
        feeds = [channel for channel in self.channels if self._is_pair_independent_feed(channel)]
        for feed in feeds:
            self._subscribe_feed(
                feed,
            )

    def _subscribe_traded_pairs_feed(self):
        """
        Subscribes all time frame unrelated feeds for traded pairs
        """
        if not self.filtered_pairs:
            return
        feeds = [channel for channel in self.channels if not self._is_pair_independent_feed(channel)]
        for feed in feeds:
            self._subscribe_feed(
                feed,
                symbols=self.filtered_pairs,
            )

    def _subscribe_watched_pairs_feed(self):
        """
        Subscribes feeds for watched pairs (only on one timeframe for multiple timeframes feeds)
        """
        if not self.watched_pairs:
            return
        feeds = [
            channel
            for channel in self.WATCHED_PAIR_CHANNELS
            if self._is_supported_channel(channel) and (channel in self.channels or not self.channels)
        ]
        for feed in feeds:
            self._subscribe_feed(
                feed,
                symbols=self.watched_pairs,
            )

    def _get_feed_default_kwargs(self):
        return {}

    def _get_feed_generator_by_feed(self):
        return {
            # Subscribed feeds
            # Unauthenticated
            Feeds.TRADES: self._get_generator("watchTrades"),
            Feeds.TICKER: self._get_generator("watchTicker"),
            Feeds.CANDLE: self._get_generator("watchOHLCV"),
            Feeds.KLINE: self._get_generator("watchOHLCV"),
            Feeds.L1_BOOK: self._get_generator("watchOrderBook"),
            Feeds.L2_BOOK: self._get_generator("watchOrderBook"),
            Feeds.L3_BOOK: self._get_generator("watchOrderBook"),
            Feeds.FUNDING: Feeds.UNSUPPORTED,
            Feeds.LIQUIDATIONS: Feeds.UNSUPPORTED,
            Feeds.OPEN_INTEREST: Feeds.UNSUPPORTED,
            Feeds.FUTURES_INDEX: Feeds.UNSUPPORTED,

            # Authenticated
            Feeds.TRANSACTIONS: self._get_generator("watchTransactions"),
            Feeds.PORTFOLIO: self._get_generator("watchBalance"),
            Feeds.ORDERS: self._get_generator("watchOrders"),
            Feeds.TRADE: self._get_generator("watchMyTrades"),
            Feeds.LEDGER: self._get_generator("watchLedger"),
            Feeds.POSITION: Feeds.UNSUPPORTED,

            # Publish feeds
            Feeds.CREATE_ORDER: self._get_generator("watchCreateOrder"),
            Feeds.CANCEL_ORDER: self._get_generator("watchCancelOrder"),
        }

    def _get_generator(self, method_name):
        return getattr(self.client, method_name) if hasattr(self.client, method_name) else Feeds.UNSUPPORTED

    def _get_callback_by_feed(self):
        return {
            # Unauthenticated
            Feeds.TRADES: self.recent_trades,
            Feeds.TICKER: self.ticker,
            Feeds.CANDLE: self.candle,
            Feeds.KLINE: self.candle,
            Feeds.FUNDING: self.funding,
            Feeds.OPEN_INTEREST: self.open_interest,
            Feeds.L1_BOOK: self.book,
            Feeds.L2_BOOK: self.book,
            Feeds.L3_BOOK: self.book,

            # Authenticated
            Feeds.TRANSACTIONS: self.transaction,
            Feeds.PORTFOLIO: self.balance,
            Feeds.ORDERS: self.orders,
            Feeds.TRADE: self.trades,
        }

    def _get_since_filter_value(self, feed, time_frame):
        if feed in self.CURRENT_TIME_FILTERED_CHANNELS:
            return self._start_time_millis
        elif feed in self.CANDLE_TIME_FILTERED_CHANNELS:
            candles_ms = commons_enums.TimeFramesMinutes[commons_enums.TimeFrames(time_frame)] * \
                commons_constants.MSECONDS_TO_MINUTE
            time_delta = self._start_time_millis % candles_ms
            return self._start_time_millis - time_delta
        return None

    def _subscribe_feed(self, feed, symbols=None, time_frame=None, since=None, limit=None, params=None):
        """
        Subscribe a new feed
        :param feed: the feed to subscribe to
        :param symbols: the feed symbols
        :param time_frame: the feed time_frame
        :param since: the ccxt feed since arg
        :param limit: the ccxt feed limit arg
        :param params: the ccxt feed param arg
        """
        try:
            feed_callback = self._get_callback_by_feed()[feed]
            feed_generator = self._get_feed_generator_by_feed()[feed]
            if Feeds.UNSUPPORTED in (feed_callback, feed_generator):
                raise KeyError
        except KeyError:
            self.logger.error(f"Impossible to subscribe to {feed}: feed not supported")
            return
        if feed in self.TIME_FRAME_PAIR_CHANNELS and time_frame is None:
            time_frame = self.min_timeframe.value
        kwargs = copy.copy(self._get_feed_default_kwargs())
        if time_frame is not None:
            kwargs["timeframe"] = time_frame
        if since is not None:
            kwargs["since"] = since
        else:
            auto_since = self._get_since_filter_value(feed, time_frame)
            if auto_since is not None:
                kwargs["since"] = auto_since
            elif feed in self.CURRENT_TIME_FILTERED_CHANNELS:
                kwargs["since"] = self._start_time_millis
            elif feed in self.CANDLE_TIME_FILTERED_CHANNELS:
                kwargs["since"] = self._start_time_millis
        if limit is not None:
            kwargs["limit"] = limit
        if params is not None:
            kwargs["params"] = params
        if symbols is not None:
            for symbol in symbols:
                kwargs["symbol"] = symbol
                # one task per symbol: ccxt_pro is not handling multi symbol generators
                self._create_task_if_necessary(feed, feed_callback, feed_generator, **kwargs)
        else:
            # no symbol param
            self._create_task_if_necessary(feed, feed_callback, feed_generator, **kwargs)

        symbols_str = f"for {', '.join(symbols)} " if symbols else ""
        time_frame_str = f"on {time_frame}" if time_frame else ""
        self.logger.debug(f"Subscribed to {feed.value} {symbols_str}{time_frame_str}")

    async def _feed_task(self, feed, callback, generator_func, *g_args, **g_kwargs):
        if not await self._wait_for_initialization(feed, *g_args, **g_kwargs):
            self.logger.error(f"Aborting {feed.value} feed connection with {g_kwargs}: "
                              f"missing required initialization data")
            return
        enable_throttling = feed in self.THROTTLED_CHANNELS and self.throttled_ws_updates != 0.0
        while not self.should_stop:
            try:
                update_data = await generator_func(*g_args, **g_kwargs)
                if update_data:
                    await callback(update_data, **g_kwargs)
                if enable_throttling:
                    # ccxt keeps updating the internal structures while waiting
                    # https://docs.ccxt.com/en/latest/ccxt.pro.manual.html?rtd_search=fetchLedger#incremental-data-structures
                    await asyncio.sleep(self.throttled_ws_updates)
            except ccxt.NetworkError as err:
                self.logger.debug(f"Can't connect to exchange websocket: {err}. "
                                  f"Retrying in {self.RECONNECT_DELAY} seconds")
                await asyncio.sleep(self.RECONNECT_DELAY)
            except Exception as err:
                self.logger.exception(
                    err,
                    True,
                    f"Unexpected error when handling {generator_func.__name__} feed: {err}"
                )
                await asyncio.sleep(self.RECONNECT_DELAY)   # avoid spamming

    def _create_task_if_necessary(self, feed, feed_callback, feed_generator, **kwargs):
        identifier = self._get_feed_identifier(feed_generator, kwargs)
        if identifier not in self.feed_tasks:
            self.logger.debug(f"Subscribing to {feed.value} with {kwargs}")
            self.feed_tasks[identifier] = asyncio.create_task(
                self._feed_task(feed, feed_callback, feed_generator, **kwargs)
            )

    async def _wait_for_initialization(self, feed, *g_args, **g_kwargs):
        if not self.is_feed_requiring_init(feed) or g_kwargs["symbol"] not in self.filtered_pairs:
            # no need to wait for pairs not in self.filtered_pairs
            return True
        is_initialized_func = None
        if feed is Feeds.CANDLE:
            def candle_is_initialized_func():
                try:
                    return self.exchange_manager.exchange_symbols_data.get_exchange_symbol_data(
                        g_kwargs["symbol"], allow_creation=False
                    ).symbol_candles[commons_enums.TimeFrames(g_kwargs["timeframe"])].candles_initialized
                except KeyError:
                    return False

            is_initialized_func = candle_is_initialized_func
        if is_initialized_func is None:
            return True
        if is_initialized_func():
            return True
        self.logger.debug(f"Waiting for initialization before starting {feed.value} feed with {g_kwargs}")
        t0 = time.time()
        while not self.should_stop and time.time() - t0 < self.FEED_INITIALIZATION_TIMEOUT:
            # add timeout
            if is_initialized_func():
                self.logger.debug(f"Starting {feed} feed with {g_kwargs}: initialization complete")
                return True
            # quickly update at first
            await asyncio.sleep(0.1 if time.time() - t0 < self.FEED_INITIALIZATION_TIMEOUT / 10 else 1)
        return is_initialized_func()

    def _get_feed_identifier(self, feed_generator, kwargs):
        return f"{feed_generator.__name__}{kwargs}"

    def _filter_exchange_pairs_and_timeframes(self):
        """
        Populates self.filtered_pairs and self.min_timeframe
        """
        self._add_exchange_symbols()
        self._init_exchange_time_frames()

    def _add_pair(self, pair, watching_only):
        """
        Add a pair to self.filtered_pairs if supported
        :param pair: the pair to add
        :param watching_only: when True add pair to watched_pairs else to filtered_pairs
        """
        if watching_only:
            self.watched_pairs.append(pair)
        else:
            self.filtered_pairs.append(pair)

    def _add_exchange_symbols(self):
        """
        Populates self.filtered_pairs from self.pairs when pair is supported by the ccxt exchange
        """
        for pair in self.pairs:
            self._add_pair(pair, watching_only=False)
        self._filter_exchange_symbols()

    def _filter_exchange_symbols(self):
        pre_filter_watched_pairs = copy.copy(self.watched_pairs)
        self.watched_pairs = [
            pair
            for pair in pre_filter_watched_pairs
            if self._is_supported_pair(pair)
        ]
        pre_filter_filtered_pairs = copy.copy(self.filtered_pairs)
        self.filtered_pairs = [
            pair
            for pair in pre_filter_filtered_pairs
            if self._is_supported_pair(pair)
        ]
        unsupported_pairs = []
        for pairs, pre_filter_pairs in (
                (self.watched_pairs, pre_filter_watched_pairs),
                (self.filtered_pairs, pre_filter_filtered_pairs)
        ):
            if len(pre_filter_filtered_pairs) > len(pairs):
                unsupported_pairs += [
                    pair
                    for pair in pre_filter_pairs
                    if pair not in pairs
                ]
        if unsupported_pairs:
            self.logger.error(f"{unsupported_pairs} pair is not supported by this exchange's websocket")

    def _add_time_frame(self, filtered_timeframes, time_frame, log_on_error):
        """
        Add a time frame to filtered_timeframes if supported
        :param time_frame: the time frame to add
        """
        if self._is_supported_time_frame(time_frame) :
            filtered_timeframes.append(time_frame)
        elif log_on_error:
            self.logger.error(f"{time_frame.value} time frame is not supported by this exchange's websocket")

    def _init_exchange_time_frames(self):
        """
        Populates self.min_timeframe from self.time_frames when time frame is supported by the ccxt exchange
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
        return self.EXCHANGE_FEEDS.get(Feeds.CANDLE, Feeds.UNSUPPORTED.value) != Feeds.UNSUPPORTED.value

    def _is_supported_pair(self, pair):
        return pair in ccxt_client_util.get_symbols(self.client)

    def _is_supported_time_frame(self, time_frame):
        return time_frame.value in ccxt_client_util.get_time_frames(self.client)

    def _is_pair_independent_feed(self, feed):
        return feed in self.PAIR_INDEPENDENT_CHANNELS

    def _convert_book_prices_to_orders(self, book_prices_and_volumes, book_side):
        """
        Convert a book_prices format : {PRICE_1: SIZE_1, PRICE_2: SIZE_2...}
        to OctoBot's order book format
        :param book_prices: an order book dictionary (order_book.SortedDict)
        :param book_side: a TradeOrderSide value
        :return: the list of order book data converted
        """
        return [
            {
                ECOBIC.PRICE.value: float(book_price_and_volume[0]),
                ECOBIC.SIZE.value: float(book_price_and_volume[1]),
                ECOBIC.SIDE.value: book_side,
            }
            for book_price_and_volume in book_prices_and_volumes
        ]

    """
    Callbacks
    """

    async def ticker(self, ticker: dict, symbol=None, **kwargs):
        """
        :param ticker: the ccxt ticker dict
        :param symbol: the feed symbol
        :param kwargs: the feed kwargs
        """
        adapted = self.adapter.adapt_ticker(ticker)
        await self.push_to_channel(
            trading_constants.TICKER_CHANNEL,
            symbol,
            adapted,
        )

    async def recent_trades(self, trades: list, symbol=None, **kwargs):
        """
        :param trades: the ccxt ticker list
        :param symbol: the feed symbol
        :param kwargs: the feed kwargs
        """
        adapted = self.adapter.adapt_public_recent_trades(trades)
        await self.push_to_channel(trading_constants.RECENT_TRADES_CHANNEL,
                                   symbol,
                                   adapted)

    async def book(self, order_book: dict, symbol=None, **kwargs):
        """
        :param order_book: the ccxt order_book dict
        :param symbol: the feed symbol
        :param kwargs: the feed kwargs
        """
        book_instance = self.get_book_instance(symbol)

        book_instance.handle_book_adds(
            self._convert_book_prices_to_orders(
                order_book[ECOBIC.ASKS.value],
                trading_enums.TradeOrderSide.SELL.value) +
            self._convert_book_prices_to_orders(
                order_book[ECOBIC.BIDS.value],
                trading_enums.TradeOrderSide.BUY.value)
        )

        await self.push_to_channel(trading_constants.ORDER_BOOK_CHANNEL,
                                   symbol,
                                   book_instance.asks,
                                   book_instance.bids,
                                   update_order_book=False)

    async def candle(self, candles: list, symbol=None, timeframe=None, **kwargs):
        """
        :param candles: the ccxt ohlcv list
        :param symbol: the feed symbol
        :param timeframe: the feed timeframe
        :param kwargs: the feed kwargs
        """
        time_frame = commons_enums.TimeFrames(timeframe)
        adapted = self.adapter.adapt_ohlcv(candles, time_frame=time_frame)
        last_candle = adapted[-1]
        if symbol not in self.watched_pairs:
            for candle in adapted:
                previous_candle = self._get_previous_open_candle(timeframe, symbol)
                is_previous_candle_closed = False
                if previous_candle is not None:
                    current_candle_time = candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value]
                    previous_candle_time = previous_candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value]
                    if previous_candle_time < current_candle_time:
                        # new candle is after the previous one: the previous one is now closed
                        is_previous_candle_closed = True
                    elif previous_candle_time > current_candle_time:
                        # should not happen: exchange feed is providing past candles after newer ones
                        # candle feed should be marked as unsupported in this exchange (at least for now)
                        self.logger.error(f"Ignored unexpected candle for {symbol} on {timeframe}: "
                                          f"candle time {current_candle_time}, "
                                          f"previous candle time: {previous_candle_time}")
                        if candle is last_candle:
                            # last candle in loop: don't go any further
                            return
                        else:
                            # go to next candle in loop
                            continue
                if is_previous_candle_closed:
                    # OHLCV_CHANNEL only takes closed candles
                    await self.push_to_channel(
                        trading_constants.OHLCV_CHANNEL,
                        time_frame,
                        symbol,
                        previous_candle
                    )
                self._register_previous_open_candle(timeframe, symbol, candle)
            await self.push_to_channel(
                trading_constants.KLINE_CHANNEL,
                time_frame,
                symbol,
                last_candle
            )

        # Push a new ticker if necessary : only push on the min timeframe
        if time_frame is self.min_timeframe:
            ticker = {
                Ectc.HIGH.value: last_candle[commons_enums.PriceIndexes.IND_PRICE_HIGH.value],
                Ectc.LOW.value: last_candle[commons_enums.PriceIndexes.IND_PRICE_LOW.value],
                Ectc.BID.value: None,
                Ectc.BID_VOLUME.value: None,
                Ectc.ASK.value: None,
                Ectc.ASK_VOLUME.value: None,
                Ectc.OPEN.value: last_candle[commons_enums.PriceIndexes.IND_PRICE_OPEN.value],
                Ectc.CLOSE.value: last_candle[commons_enums.PriceIndexes.IND_PRICE_CLOSE.value],
                Ectc.LAST.value: last_candle[commons_enums.PriceIndexes.IND_PRICE_CLOSE.value],
                Ectc.PREVIOUS_CLOSE.value: None,
                Ectc.BASE_VOLUME.value: last_candle[commons_enums.PriceIndexes.IND_PRICE_VOL.value],
                Ectc.TIMESTAMP.value: self.exchange.get_exchange_current_time(),
            }
            await self.push_to_channel(
                trading_constants.TICKER_CHANNEL,
                symbol,
                ticker
            )

    async def funding(self, funding: dict, symbol=None, **kwargs):
        """
        Unsupported, feed list https://docs.ccxt.com/en/latest/ccxt.pro.manual.html?rtd_search=fetchLedger#prerequisites
        :param funding: the ccxt funding dict
        :param symbol: the feed symbol
        :param kwargs: the feed kwargs
        """
        # TODO update this when supported
        raise NotImplementedError("funding callback is not implemented")
        adapted = self.adapter.parse_funding_rate(funding)
        predicted_funding_rate = \
            adapted.get(trading_enums.ExchangeConstantsFundingColumns.PREDICTED_FUNDING_RATE.value,
                        trading_constants.NaN)
        await self.push_to_channel(
            trading_constants.FUNDING_CHANNEL,
            symbol,
            decimal.Decimal(adapted[trading_enums.ExchangeConstantsFundingColumns.FUNDING_RATE.value]),
            predicted_funding_rate=decimal.Decimal(str(predicted_funding_rate or trading_constants.NaN)),
            next_funding_time=adapted[trading_enums.ExchangeConstantsFundingColumns.NEXT_FUNDING_TIME.value],
            last_funding_time=adapted[trading_enums.ExchangeConstantsFundingColumns.LAST_FUNDING_TIME.value]
        )

    async def open_interest(self, open_interest: dict, symbol=None, **kwargs):
        """
        Unsupported, feed list https://docs.ccxt.com/en/latest/ccxt.pro.manual.html?rtd_search=fetchLedger#prerequisites
        :param open_interest: the ccxt open_interest dict
        :param symbol: the feed symbol
        :param kwargs: the feed kwargs
        """
        # TODO update this when supported
        raise NotImplementedError("open_interest callback is not implemented")

    async def index(self, index: dict, symbol=None, **kwargs):
        """
        Unsupported, feed list https://docs.ccxt.com/en/latest/ccxt.pro.manual.html?rtd_search=fetchLedger#prerequisites
        :param index: the ccxt index dict
        :param symbol: the feed symbol
        :param kwargs: the feed kwargs
        """
        # TODO update this when supported
        raise NotImplementedError("index callback is not implemented")

    async def orders(self, orders: list, **kwargs):
        """
        :param orders: the ccxt orders list
        :param kwargs: the feed kwargs
        """
        # TODO update this when supported (ccxt is supporting it)
        raise NotImplementedError("orders callback is not implemented")
        adapted = [self.adapter.adapt_order(order) for order in orders]
        await self.push_to_channel(trading_constants.ORDERS_CHANNEL, adapted)

    async def trades(self, trades: list, **kwargs):
        """
        :param trades: the ccxt trades list
        :param kwargs: the feed kwargs
        """
        # TODO update this when supported (ccxt is supporting it)
        raise NotImplementedError("trades callback is not implemented")
        adapted = self.adapter.adapt_trades(self.exchange.parse_trade(trades))
        await self.push_to_channel(trading_constants.TRADES_CHANNEL, adapted)

    async def balance(self, balance: dict, **kwargs):
        """
        :param balance: the ccxt balance dict
        :param kwargs: the feed kwargs
        """
        # TODO update this when supported (ccxt is supporting it)
        raise NotImplementedError("balance callback is not implemented")
        await self.push_to_channel(trading_constants.BALANCE_CHANNEL,
                                   self.adapter.parse_balance(balance.balance))

    async def transaction(self, transaction: dict, **kwargs):
        """
        :param transaction: the ccxt transaction dict
        :param kwargs: the feed kwargs
        """
        # TODO update this when supported (ccxt is supporting it). Use watchLedger ?
        raise NotImplementedError("transaction callback is not implemented")

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
