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

import cryptofeed
import cryptofeed.connection_handler
import cryptofeed.callback as cryptofeed_callbacks
import cryptofeed.defines as cryptofeed_constants
import cryptofeed.exchanges as cryptofeed_exchanges

import octobot_commons
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
        Feeds.TRADES: [Feeds.TICKER]
    }

    def __init__(self, config: object, exchange_manager: object):
        super().__init__(config, exchange_manager)
        self.channels = []

        self.callbacks = {}
        self.candle_callback = None

        self.filtered_pairs = []
        self.filtered_timeframes = []
        self.min_timeframe = None

        self._fix_signal_handler()

        # Manage cryptofeed loggers
        self.client_logger = logging.getLogger(f"WebSocketClient - {self.name}")
        self.client_logger.setLevel(logging.WARNING)
        self._fix_logger()

        self.client = None
        commons_logging.set_logging_level(self.CRYPTOFEED_LOGGERS, logging.WARNING)

        self.callback_by_feed = {
            cryptofeed_constants.TRADES: cryptofeed_callbacks.TradeCallback(self.trade),
            cryptofeed_constants.TICKER: cryptofeed_callbacks.TickerCallback(self.ticker),
            cryptofeed_constants.CANDLES: cryptofeed_callbacks.CandleCallback(self.candle),  # pylint: disable=E1101
            # cryptofeed_constants.L2_BOOK: cryptofeed_callbacks.BookCallback(self.book),
            # cryptofeed_constants.L3_BOOK: cryptofeed_callbacks.BookCallback(self.book),
            # cryptofeed_constants.FUNDING: cryptofeed_callbacks.FundingCallback(self.funding),
            # cryptofeed_constants.LIQUIDATIONS: cryptofeed_callbacks.LiquidationCallback(self.liquidations),
            # cryptofeed_constants.BOOK_DELTA: cryptofeed_callbacks.BookUpdateCallback(self.delta),
            # cryptofeed_constants.VOLUME: cryptofeed_callbacks.VolumeCallback(self.volume),
            # cryptofeed_constants.OPEN_INTEREST: cryptofeed_callbacks.OpenInterestCallback(self.open_interest),
            # cryptofeed_constants.FUTURES_INDEX: cryptofeed_callbacks.FuturesIndexCallback(self.futures_index),
            # cryptofeed_constants.MARKET_INFO: cryptofeed_callbacks.MarketInfoCallback(self.market_info),
            # cryptofeed_constants.TRANSACTIONS: cryptofeed_callbacks.TransactionsCallback(self.transactions),
        }
        self._set_async_callbacks()

        # Create cryptofeed FeedHandler instance
        self._create_client()

        # Creates cryptofeed exchange instance
        self.cryptofeed_exchange = cryptofeed_exchanges.EXCHANGE_MAP[self.get_feed_name()](config=self.client.config)

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

    async def stop(self):
        """
        Reimplementation of self.client.stop() without calling loop.run_until_complete()
        """
        try:
            for feed in self.client.feeds:
                feed.stop()
            for feed in self.client.feeds:
                await feed.shutdown()
            if self.client.raw_data_collection:
                self.client.raw_data_collection.stop()
        except Exception as e:
            self.logger.error(f"Failed to stop websocket feed : {e}")

    async def close(self):
        """
        Can't call self.client.close() because it uses loop operations
        """
        try:
            self.client = None
        except Exception as e:
            self.logger.error(f"Failed to close websocket feed : {e}")

    def add_pairs(self, pairs):
        """
        Add new pairs to self.filtered_pairs
        :param pairs: the list of pair to add
        """
        for pair in pairs:
            self._add_pair(self.get_exchange_pair(pair))

    def add_time_frames(self, time_frames):
        """
        Add new time_frames to self.filtered_time_frames
        :param time_frames: the list of time_frame to add
        """
        for time_frame in time_frames:
            self._add_time_frame(time_frame)

    def subscribe_feeds(self):
        if self.EXCHANGE_FEEDS.get(Feeds.CANDLE) and self.is_feed_supported(self.EXCHANGE_FEEDS.get(Feeds.CANDLE)):
            self.subscribe_candle_feed(self.pairs)
    async def reset(self):
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
            self._subscribe_all_pairs_feed()
            self._start_client(should_create_loop=False)
        except Exception as e:
            self.logger.error(f"Failed to reconnect to websocket : {e}")

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
        self.client = cryptofeed.FeedHandler()

    def _init_client(self):
        """
        Prepares client configuration and instantiates client feeds
        """
        try:
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
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            self.client.run(start_loop=should_create_loop)
        except Exception as e:
            self.logger.error(f"Failed to start websocket feed : {e}")
        self.logger.warning("Websocket master thread terminated, this should not happen during bot run"
                            " with a valid configuration")

    def _subscribe_feeds(self):
        """
        Subscribe time frame related feeds and time frame unrelated feeds
        """
        if self._should_run_candle_feed():
            self.candle_callback = self.callback_by_feed[self.EXCHANGE_FEEDS[Feeds.CANDLE]]
            self._subscribe_candle_feed()

        # drop unsupported channels
        self.channels = [channel for channel in self.channels if channel not in [Feeds.UNSUPPORTED.value,
                                                                                 self.EXCHANGE_FEEDS.get(
                                                                                     Feeds.CANDLE)]]
        self.callbacks = {
            channel: self.callback_by_feed[channel]
            for channel in self.channels
            if self.callback_by_feed.get(channel) and not self.should_ignore_feed(self.callback_by_feed[channel])
        }
        self._subscribe_all_pairs_feed()

    def _subscribe_candle_feed(self):
        """
        Subscribes a new candle feed for each time frame
        """
        for time_frame in self.time_frames:
            self.client.add_feed(self.get_feed_name(),
                                 candle_interval=time_frame.value,
                                 candle_closed_only=False,
                                 symbols=self.filtered_pairs,
                                 log_message_on_error=True,
                                 channels=[cryptofeed_constants.CANDLES],
                                 callbacks={cryptofeed_constants.CANDLES: self.candle_callback})
            self.logger.debug(f"Subscribed to the {time_frame.value} time frame for {', '.join(self.filtered_pairs)}")

    def _subscribe_all_pairs_feed(self):
        """
        Subscribes all time frame unrelated feeds
        """
        self.client.add_feed(self.get_feed_name(),
                             symbols=self.filtered_pairs,
                             channels=self.channels,
                             callbacks=self.callbacks)
        for channel in self.channels:
            self.logger.debug(f"Subscribed to {channel}")

    def _filter_exchange_pairs_and_timeframes(self):
        """
        Populates self.filtered_pairs and self.filtered_timeframes
        """
        self._filter_exchange_symbols()
        self._filter_exchange_time_frames()

    def _add_pair(self, pair):
        """
        Add a pair to self.filtered_pairs if supported
        :param pair: the pair to add
        """
        if self._is_supported_pair(pair):
            self.filtered_pairs.append(pair)
        else:
            self.logger.error(f"{self.get_pair_from_exchange(pair)} pair is not supported by this exchange's websocket")

    def _filter_exchange_symbols(self):
        """
        Populates self.filtered_pairs from self.pairs when pair is supported by the cryptofeed exchange
        """
        for pair in self.pairs:
            self._add_pair(pair)

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
            # await self.push_to_channel(trading_constants.ORDER_BOOK_TICKER_CHANNEL,
            #                            symbol=symbol,
            #                            ask_quantity=None,
            #                            ask_price=ask,
            #                            bid_quantity=None,
            #                            bid_price=bid)

    async def trade(self, feed, symbol, order_id, timestamp, side, amount, price, receipt_timestamp):
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

    async def volume(self, **kwargs):
        pass

    async def futures_index(self, **kwargs):
        pass

    async def market_info(self, **kwargs):
        pass  # Coingecko only
