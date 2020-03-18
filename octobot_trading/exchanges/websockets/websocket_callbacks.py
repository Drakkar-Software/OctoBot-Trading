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

from octobot_trading.channels.balance import BalanceProducer
from octobot_trading.channels.funding import FundingProducer
from octobot_trading.channels.kline import KlineProducer
from octobot_trading.channels.ohlcv import OHLCVProducer
from octobot_trading.channels.order_book import OrderBookProducer
from octobot_trading.channels.orders import OrdersProducer
from octobot_trading.channels.positions import PositionsProducer
from octobot_trading.channels.price import MarkPriceProducer
from octobot_trading.channels.recent_trade import RecentTradeProducer
from octobot_trading.channels.ticker import TickerProducer
from octobot_commons.logging.logging_util import get_logger
from octobot_trading.channels.trades import TradesProducer

from octobot_trading.enums import ExchangeConstantsOrderColumns as ECOC, ExchangeConstantsTickersColumns


class OrderBookCallBack(OrderBookProducer):
    def __init__(self, parent, channel, pair):
        super().__init__(channel)
        self.parent = parent
        self.pair = pair
        self.logger = get_logger(f"WebSocket"
                                 f" - {self.parent.exchange_manager.exchange_name}"
                                 f" - {self.__class__.__name__}")

    async def callback(self, feed, asks, bids, timestamp):
        try:
            asyncio.run_coroutine_threadsafe(self.push(symbol=self.pair,
                                                       asks=asks,
                                                       bids=bids), asyncio.get_event_loop())
        except Exception as e:
            self.logger.error(f"Callback failed : {e}")

    async def modify(self, **kwargs) -> None:
        pass


class RecentTradesCallBack(RecentTradeProducer):
    def __init__(self, parent, channel, pair):
        super().__init__(channel)
        self.parent = parent
        self.pair = pair
        self.logger = get_logger(f"WebSocket"
                                 f" - {self.parent.exchange_manager.exchange_name}"
                                 f" - {self.__class__.__name__}")

    async def callback(self, recent_trades):
        try:
            asyncio.run_coroutine_threadsafe(self.push(symbol=self.pair,
                                                       recent_trades=recent_trades),
                                             asyncio.get_event_loop())
        except Exception as e:
            self.logger.error(f"Callback failed : {e}")

    async def modify(self, **kwargs) -> None:
        pass


class TickersCallBack(TickerProducer):
    def __init__(self, parent, channel, pair):
        super().__init__(channel)
        self.parent = parent
        self.pair = pair
        self.logger = get_logger(f"WebSocket"
                                 f" - {self.parent.exchange_manager.exchange_name}"
                                 f" - {self.__class__.__name__}")

    async def callback(self, ticker):
        try:
            asyncio.run_coroutine_threadsafe(self.push(symbol=self.pair,
                                                       ticker=ticker),
                                             asyncio.get_event_loop())
        except Exception as e:
            self.logger.error(f"Callback failed : {e}")

    async def modify(self, **kwargs) -> None:
        pass


class OHLCVCallBack(OHLCVProducer):
    def __init__(self, parent, channel, pair, time_frame):
        super().__init__(channel)
        self.parent = parent
        self.pair = pair
        self.time_frame = time_frame
        self.logger = get_logger(f"WebSocket"
                                 f" - {self.parent.exchange_manager.exchange_name}"
                                 f" - {self.__class__.__name__}")

    async def callback(self, candle):
        try:
            asyncio.run_coroutine_threadsafe(self.push(symbol=self.pair,
                                                       time_frame=self.time_frame,
                                                       candle=[candle],
                                                       partial=True), asyncio.get_event_loop())
        except Exception as e:
            self.logger.error(f"Callback failed : {e}")

    async def modify(self, **kwargs) -> None:
        pass


class KlineCallBack(KlineProducer):
    def __init__(self, parent, channel, pair, time_frame):
        super().__init__(channel)
        self.parent = parent
        self.pair = pair
        self.time_frame = time_frame
        self.logger = get_logger(f"WebSocket"
                                 f" - {self.parent.exchange_manager.exchange_name}"
                                 f" - {self.__class__.__name__}")

    async def callback(self, kline):
        try:
            asyncio.run_coroutine_threadsafe(self.push(symbol=self.pair,
                                                       time_frame=self.time_frame,
                                                       kline=kline), asyncio.get_event_loop())
        except Exception as e:
            self.logger.error(f"Callback failed : {e}")

    async def modify(self, **kwargs) -> None:
        pass


class FundingCallBack(FundingProducer):
    def __init__(self, parent, channel, pair):
        super().__init__(channel)
        self.parent = parent
        self.pair = pair
        self.logger = get_logger(f"WebSocket"
                                 f" - {self.parent.exchange_manager.exchange_name}"
                                 f" - {self.__class__.__name__}")

    async def callback(self, funding_rate, next_funding_time, timestamp):
        try:
            asyncio.run_coroutine_threadsafe(self.push(symbol=self.pair,
                                                       funding_rate=funding_rate,
                                                       next_funding_time=next_funding_time,
                                                       timestamp=timestamp), asyncio.get_event_loop())
        except Exception as e:
            self.logger.error(f"Callback failed : {e}")

    async def modify(self, **kwargs) -> None:
        pass


class MarkPriceCallBack(MarkPriceProducer):
    def __init__(self, parent, channel, pair):
        super().__init__(channel)
        self.parent = parent
        self.pair = pair
        self.logger = get_logger(f"WebSocket"
                                 f" - {self.parent.exchange_manager.exchange_name}"
                                 f" - {self.__class__.__name__}")

    async def callback(self, mark_price):
        try:
            asyncio.run_coroutine_threadsafe(self.push(symbol=self.pair,
                                                       mark_price=mark_price),
                                             asyncio.get_event_loop())
        except Exception as e:
            self.logger.error(f"Callback failed : {e}")

    async def modify(self, **kwargs) -> None:
        pass


class BalanceCallBack(BalanceProducer):
    def __init__(self, parent, channel):
        super().__init__(channel)
        self.parent = parent
        self.logger = get_logger(f"WebSocket"
                                 f" - {self.parent.exchange_manager.exchange_name}"
                                 f" - {self.__class__.__name__}")

    async def callback(self, balance):
        try:
            asyncio.run_coroutine_threadsafe(self.push(balance=balance), asyncio.get_event_loop())
        except Exception as e:
            self.logger.error(f"Callback failed : {e}")

    async def modify(self, **kwargs) -> None:
        pass


class OrdersCallBack(OrdersProducer):
    def __init__(self, parent, channel):
        super().__init__(channel)
        self.parent = parent
        self.logger = get_logger(f"WebSocket"
                                 f" - {self.parent.exchange_manager.exchange_name}"
                                 f" - {self.__class__.__name__}")

    async def callback(self, orders):
        try:
            asyncio.run_coroutine_threadsafe(self.push(orders=orders), asyncio.get_event_loop())
        except Exception as e:
            self.logger.error(f"Callback failed : {e}")

    async def modify(self, **kwargs) -> None:
        pass


class PositionsCallBack(PositionsProducer):
    def __init__(self, parent, channel):
        super().__init__(channel)
        self.parent = parent
        self.logger = get_logger(f"WebSocket"
                                 f" - {self.parent.exchange_manager.exchange_name}"
                                 f" - {self.__class__.__name__}")

    async def callback(self, positions, is_closed=False, is_liquidated=False):
        try:
            asyncio.run_coroutine_threadsafe(self.push(positions=positions,
                                                       is_closed=is_closed,
                                                       is_liquidated=is_liquidated), asyncio.get_event_loop())
        except Exception as e:
            self.logger.error(f"Callback failed : {e}")

    async def modify(self, **kwargs) -> None:
        pass


class ExecutionsCallBack(TradesProducer):
    def __init__(self, parent, channel):
        super().__init__(channel)
        self.parent = parent
        self.logger = get_logger(f"WebSocket"
                                 f" - {self.parent.exchange_manager.exchange_name}"
                                 f" - {self.__class__.__name__}")

    async def callback(self, trades):
        try:
            asyncio.run_coroutine_threadsafe(self.push(trades=trades, old_trade=False), asyncio.get_event_loop())
        except Exception as e:
            self.logger.error(f"Callback failed : {e}")

    async def modify(self, **kwargs) -> None:
        pass
