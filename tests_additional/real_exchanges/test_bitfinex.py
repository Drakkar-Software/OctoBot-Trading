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

import pytest

from octobot_commons.enums import TimeFrames, PriceIndexes
from octobot_trading.enums import ExchangeConstantsMarketStatusColumns as Ecmsc, \
    ExchangeConstantsOrderBookInfoColumns as Ecobic, ExchangeConstantsOrderColumns as Ecoc, \
    ExchangeConstantsTickersColumns as Ectc
from tests_additional.real_exchanges.real_exchange_tester import RealExchangeTester
# required to catch async loop context exceptions
from tests import event_loop

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


class TestBitfinexRealExchangeTester(RealExchangeTester):
    EXCHANGE_NAME = "bitfinex2"
    SYMBOL = "BTC/USD"
    SYMBOL_2 = "ETH/BTC"
    SYMBOL_3 = "XRP/BTC"
    DEFAULT_CANDLE_LIMIT = 100
    SLEEP_TIME = 10

    async def test_time_frames(self):
        await asyncio.sleep(self.SLEEP_TIME)  # prevent rate api limit
        time_frames = await self.time_frames()
        assert all(time_frame in time_frames for time_frame in (
            TimeFrames.ONE_MINUTE.value,
            TimeFrames.FIVE_MINUTES.value,
            TimeFrames.FIFTEEN_MINUTES.value,
            TimeFrames.THIRTY_MINUTES.value,
            TimeFrames.ONE_HOUR.value,
            TimeFrames.FOUR_HOURS.value,
            TimeFrames.SIX_HOURS.value,
            TimeFrames.TWELVE_HOURS.value,
            TimeFrames.ONE_DAY.value,
            TimeFrames.ONE_WEEK.value,
            TimeFrames.ONE_MONTH.value
        ))

    async def test_get_market_status(self):
        # await asyncio.sleep(self.SLEEP_TIME)  # prevent rate api limit
        for market_status in await self.get_market_statuses():
            assert market_status
            assert market_status[Ecmsc.SYMBOL.value] in (self.SYMBOL, self.SYMBOL_2, self.SYMBOL_3)
            assert market_status[Ecmsc.PRECISION.value]
            assert int(market_status[Ecmsc.PRECISION.value][Ecmsc.PRECISION_AMOUNT.value]) == \
                   market_status[Ecmsc.PRECISION.value][Ecmsc.PRECISION_AMOUNT.value]
            assert int(market_status[Ecmsc.PRECISION.value][Ecmsc.PRECISION_PRICE.value]) == \
                   market_status[Ecmsc.PRECISION.value][Ecmsc.PRECISION_PRICE.value]
            assert all(elem in market_status[Ecmsc.LIMITS.value]
                       for elem in (Ecmsc.LIMITS_AMOUNT.value,
                                    Ecmsc.LIMITS_PRICE.value,
                                    Ecmsc.LIMITS_COST.value))
            self.check_market_status_limits(market_status,
                                            normal_price_min=1e-08,
                                            normal_cost_min=1e-13,  # weirdly low value
                                            low_cost_min=1e-08,  # higher min cost on lower prices, makes no sense
                                            # but is compatible
                                            expect_invalid_price_limit_values=False,
                                            enable_price_and_cost_comparison=False    # because of low cose value in
                                            # normal prices but not in low ones
                                            )

    async def test_get_symbol_prices(self):
        await asyncio.sleep(self.SLEEP_TIME)  # prevent rate api limit
        # without limit
        symbol_prices = await self.get_symbol_prices()
        # no idea why 4 candles less than asked for but it seems to be a bitfinex issue
        candle_limit_error = 4
        assert len(symbol_prices) == self.DEFAULT_CANDLE_LIMIT - candle_limit_error
        # check candles order (oldest first)
        self.ensure_elements_order(symbol_prices, PriceIndexes.IND_PRICE_TIME.value)
        # check last candle is the current candle
        assert symbol_prices[-1][PriceIndexes.IND_PRICE_TIME.value] >= self.get_time() - self.get_allowed_time_delta()

        # try with candles limit (used in candled updater)
        symbol_prices = await self.get_symbol_prices(limit=200)
        assert len(symbol_prices) == 200 - candle_limit_error
        # check candles order (oldest first)
        self.ensure_elements_order(symbol_prices, PriceIndexes.IND_PRICE_TIME.value)
        # check last candle is the current candle
        assert symbol_prices[-1][PriceIndexes.IND_PRICE_TIME.value] >= self.get_time() - self.get_allowed_time_delta()

    async def test_get_kline_price(self):
        # await asyncio.sleep(10) # prevent rate api limit
        kline_price = await self.get_kline_price()
        assert len(kline_price) == 1
        assert len(kline_price[0]) == 6
        kline_start_time = kline_price[0][PriceIndexes.IND_PRICE_TIME.value]
        # assert kline is the current candle
        assert kline_start_time >= self.get_time() - self.get_allowed_time_delta()

    async def test_get_order_book(self):
        await asyncio.sleep(self.SLEEP_TIME)  # prevent rate api limit
        # bitfinex2 only supports 1, 25 and 100 size
        # https://docs.bitfinex.com/reference#rest-public-book
        order_book = await self.get_order_book(limit=25)
        assert len(order_book[Ecobic.ASKS.value]) == 25
        assert len(order_book[Ecobic.ASKS.value][0]) == 2
        assert len(order_book[Ecobic.BIDS.value]) == 25
        assert len(order_book[Ecobic.BIDS.value][0]) == 2

    async def test_get_recent_trades(self):
        await asyncio.sleep(self.SLEEP_TIME)  # prevent rate api limit
        recent_trades = await self.get_recent_trades()
        assert len(recent_trades) == 50
        # check trades order (oldest first)
        self.ensure_elements_order(recent_trades, Ecoc.TIMESTAMP.value)

    async def test_get_price_ticker(self):
        await asyncio.sleep(self.SLEEP_TIME)  # prevent rate api limit
        ticker = await self.get_price_ticker()
        self._check_ticker(ticker, self.SYMBOL, check_content=True)

    async def test_get_all_currencies_price_ticker(self):
        await asyncio.sleep(self.SLEEP_TIME)  # prevent rate api limit
        tickers = await self.get_all_currencies_price_ticker()
        for symbol, ticker in tickers.items():
            self._check_ticker(ticker, symbol)

    @staticmethod
    def _check_ticker(ticker, symbol, check_content=False):
        assert ticker[Ectc.SYMBOL.value] == symbol
        assert all(key in ticker for key in (
            Ectc.HIGH.value,
            Ectc.LOW.value,
            Ectc.BID.value,
            Ectc.BID_VOLUME.value,
            Ectc.ASK.value,
            Ectc.ASK_VOLUME.value,
            Ectc.OPEN.value,
            Ectc.CLOSE.value,
            Ectc.LAST.value,
            Ectc.PREVIOUS_CLOSE.value
        ))
        if check_content:
            assert ticker[Ectc.HIGH.value]
            assert ticker[Ectc.LOW.value]
            assert ticker[Ectc.BID.value]
            assert ticker[Ectc.BID_VOLUME.value] is None
            assert ticker[Ectc.ASK.value]
            assert ticker[Ectc.ASK_VOLUME.value] is None
            assert ticker[Ectc.OPEN.value]
            assert ticker[Ectc.CLOSE.value]
            assert ticker[Ectc.LAST.value]
            assert ticker[Ectc.PREVIOUS_CLOSE.value] is None
            assert ticker[Ectc.BASE_VOLUME.value]
            assert ticker[Ectc.TIMESTAMP.value]
            # open is None on this exchange
            RealExchangeTester.check_ticker_typing(ticker, check_open=False)
