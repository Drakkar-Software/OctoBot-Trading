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

from octobot_trading.channels.ohlcv import OHLCVProducer
from octobot_trading.channels.order_book import OrderBookProducer
from octobot_trading.channels.recent_trade import RecentTradeProducer
from octobot_trading.channels.ticker import TickerProducer
from octobot_commons.logging.logging_util import get_logger

from octobot_trading.enums import ExchangeConstantsOrderColumns as ECOC


class OrderBookCallBack(OrderBookProducer):
    def __init__(self, parent, channel):
        super().__init__(channel)
        self.parent = parent
        self.logger = get_logger(f"WebSocket"
                                 f" - {self.parent.exchange_manager.exchange.name}"
                                 f" - {self.__class__.__name__}")

    async def l2_order_book_callback(self, _, pair, asks, bids, timestamp):
        try:
            asyncio.run_coroutine_threadsafe(self.push(symbol=pair,
                                                       asks=asks,
                                                       bids=bids), asyncio.get_event_loop())
        except Exception as e:
            self.logger.error(f"Callaback failed : {e}")


class RecentTradesCallBack(RecentTradeProducer):
    def __init__(self, parent, channel):
        super().__init__(channel)
        self.parent = parent
        self.logger = get_logger(f"WebSocket"
                                 f" - {self.parent.exchange_manager.exchange.name}"
                                 f" - {self.__class__.__name__}")

    async def recent_trades_callback(self, _, pair, side, amount, price, timestamp):
        try:
            asyncio.run_coroutine_threadsafe(self.push(symbol=pair, recent_trades=[{ECOC.SYMBOL.value: pair,
                                                                                   ECOC.SIDE.value: side,
                                                                                   ECOC.AMOUNT.value: amount,
                                                                                   ECOC.PRICE.value: price,
                                                                                   ECOC.TIMESTAMP.value: timestamp}]),
                                             asyncio.get_event_loop())
        except Exception as e:
            self.logger.error(f"Callaback failed : {e}")


class TickersCallBack(TickerProducer):
    def __init__(self, parent, channel):
        super().__init__(channel)
        self.parent = parent
        self.logger = get_logger(f"WebSocket"
                                 f" - {self.parent.exchange_manager.exchange.name}"
                                 f" - {self.__class__.__name__}")

    async def tickers_callback(self, _, pair, bid, ask, last, timestamp):
        try:
            asyncio.run_coroutine_threadsafe(self.push(symbol=pair,
                                                       ticker=(pair,
                                                               bid,
                                                               ask,
                                                               last,
                                                               timestamp)), asyncio.get_event_loop())
        except Exception as e:
            self.logger.error(f"Callaback failed : {e}")


class OHLCVCallBack(OHLCVProducer):
    def __init__(self, parent, channel, time_frame):
        super().__init__(channel)
        self.parent = parent
        self.time_frame = time_frame
        self.logger = get_logger(f"WebSocket"
                                 f" - {self.parent.exchange_manager.exchange.name}"
                                 f" - {self.__class__.__name__}")

    async def ohlcv_callback(self, data=None):
        try:
            for symbol in data:
                asyncio.run_coroutine_threadsafe(self.push(symbol=symbol,
                                                           time_frame=self.time_frame,
                                                           candle=data[symbol]), asyncio.get_event_loop())
        except Exception as e:
            self.logger.error(f"Callaback failed : {e}")
