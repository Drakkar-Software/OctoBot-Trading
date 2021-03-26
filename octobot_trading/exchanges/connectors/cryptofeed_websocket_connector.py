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
import cryptofeed.callback as cryptofeed_callbacks
import cryptofeed.defines as cryptofeed_constants

import octobot_commons
import octobot_commons.enums as commons_enums
import octobot_commons.logging as commons_logging
import octobot_commons.symbol_util as symbol_util
import octobot_trading.constants as trading_constants
import octobot_trading.enums as trading_enums
import octobot_trading.exchanges.abstract_websocket_exchange as abstract_websocket
from octobot_trading.enums import WebsocketFeeds as Feeds
from octobot_trading.enums import ExchangeConstantsOrderBookInfoColumns as ECOBIC


class CryptofeedWebsocketConnector(abstract_websocket.AbstractWebsocketExchange):
    LOGGERS = ["feedhandler"]
    CRYPTOFEED_DEFAULT_MARKET_SEPARATOR = "-"

    def __init__(self, config: object, exchange_manager: object):
        super().__init__(config, exchange_manager)
        self.fix_signal_handler()
        self.client = cryptofeed.FeedHandler()
        commons_logging.set_logging_level(self.LOGGERS, logging.DEBUG)

        self.callback_by_feed = {
            cryptofeed_constants.TRADES: cryptofeed_callbacks.TradeCallback(self.trade),
            cryptofeed_constants.TICKER: cryptofeed_callbacks.TickerCallback(self.ticker),
            cryptofeed_constants.CANDLES: cryptofeed_callbacks.CandleCallback(self.candle),  # pylint: disable=E1101
            cryptofeed_constants.L2_BOOK: cryptofeed_callbacks.BookCallback(self.book),
            cryptofeed_constants.L3_BOOK: cryptofeed_callbacks.BookCallback(self.book),
            cryptofeed_constants.FUNDING: cryptofeed_callbacks.FundingCallback(self.funding),
            cryptofeed_constants.LIQUIDATIONS: cryptofeed_callbacks.LiquidationCallback(self.liquidations),
            cryptofeed_constants.BOOK_DELTA: cryptofeed_callbacks.BookUpdateCallback(self.delta),
            cryptofeed_constants.VOLUME: cryptofeed_callbacks.VolumeCallback(self.volume),
            cryptofeed_constants.OPEN_INTEREST: cryptofeed_callbacks.OpenInterestCallback(self.open_interest),
            cryptofeed_constants.FUTURES_INDEX: cryptofeed_callbacks.FuturesIndexCallback(self.futures_index),
            cryptofeed_constants.MARKET_INFO: cryptofeed_callbacks.MarketInfoCallback(self.market_info),
            cryptofeed_constants.TRANSACTIONS: cryptofeed_callbacks.TransactionsCallback(self.transactions),
        }

    @classmethod
    def get_feed_name(cls):
        raise NotImplementedError("get_feed_name not implemented")

    def fix_signal_handler(self):
        """
        Websocket are started in a new thread thus signal handle cannot be used
        add_signal_handler() can only be called from the main thread
        """
        cryptofeed.feedhandler.SIGNALS = ()

    def subscribe_candle_feed(self, exchange_symbols):
        candle_callback = self.callback_by_feed[self.EXCHANGE_FEEDS[Feeds.CANDLE]]

        for time_frame in self.time_frames:
            self.client.add_feed(self.get_feed_name(),
                                 candle_interval=time_frame.value,
                                 candle_closed_only=False,
                                 symbols=exchange_symbols,
                                 channels=[cryptofeed_constants.CANDLES],  # pylint: disable=E1101
                                 callbacks={cryptofeed_constants.CANDLES: candle_callback})  # pylint: disable=E1101

    def subscribe_feeds(self):
        exchange_symbols = [
            self.get_exchange_pair(pair)
            for pair in self.pairs
        ]

        if self.EXCHANGE_FEEDS.get(Feeds.CANDLE):
            self.subscribe_candle_feed(exchange_symbols)

        # drop unsupported channels
        self.channels = [channel for channel in self.channels if channel not in [Feeds.UNSUPPORTED,
                                                                                 self.EXCHANGE_FEEDS.get(
                                                                                     Feeds.CANDLE)]]
        callbacks = {
            channel: self.callback_by_feed[channel]
            for channel in self.channels
        }
        self.client.add_feed(self.get_feed_name(),
                             symbols=exchange_symbols,
                             channels=self.channels,
                             callbacks=callbacks)

    def start(self):
        try:
            self.subscribe_feeds()
        except Exception as e:
            self.logger.error(f"Failed to subscribe when creating websocket feed : {e}")
        try:
            # without this two lines `There is no current event loop in thread`
            # is raised when calling `client.run()`
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.client.run()
        except Exception as e:
            self.logger.error(f"Failed to start websocket feed : {e}")

    async def ticker(self, feed, symbol, bid, ask, timestamp, receipt_timestamp):
        if symbol:
            symbol = self.get_pair_from_exchange(symbol)
            await self.push_to_channel(trading_constants.ORDER_BOOK_TICKER_CHANNEL,
                                       symbol=symbol,
                                       ask_quantity=ask,
                                       ask_price=None,
                                       bid_quantity=bid,
                                       bid_price=None)

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

    def _convert_book_prices_to_orders(self, book_prices, book_side):
        return [
            {
                ECOBIC.PRICE.value: float(order_price),
                ECOBIC.SIZE.value: float(order_size),
                ECOBIC.SIDE.value: book_side,
            }
            for order_price, order_size in book_prices.items()
        ]

    async def candle(self, feed, symbol, start, stop, interval, trades, open_price, close_price, high_price,
                     low_price, volume, closed, timestamp, receipt_timestamp):
        if symbol:
            symbol = self.get_pair_from_exchange(symbol)
            time_frame = commons_enums.TimeFrames(interval)
            candle = [
                timestamp,
                float(open_price),
                float(high_price),
                float(low_price),
                float(close_price),
                float(volume),
            ]
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

    async def transactions(self, **kwargs):
        pass  # Whale alert only

    def get_pair_from_exchange(self, pair) -> str:
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
