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
import pytest

from octobot_commons.enums import TimeFrames, PriceIndexes
from octobot_trading.enums import ExchangeConstantsMarketStatusColumns as Ecmsc, \
    ExchangeConstantsOrderBookInfoColumns as Ecobic, ExchangeConstantsOrderColumns as Ecoc, \
    ExchangeConstantsTickersColumns as Ectc
import octobot_trading.errors
from tests_additional.real_exchanges.real_exchange_tester import RealExchangeTester
# required to catch async loop context exceptions
from tests import event_loop

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


class TestBingxRealExchangeTester(RealExchangeTester):
    EXCHANGE_NAME = "bingx"
    SYMBOL = "BTC/USDT"
    SYMBOL_2 = "ETH/BTC"
    SYMBOL_3 = "SHIB/USDT"

    async def _test_time_frames(self):
        time_frames = await self.time_frames()
        assert all(time_frame in time_frames for time_frame in (
            TimeFrames.ONE_MINUTE.value,
            TimeFrames.THREE_MINUTES.value,
            TimeFrames.FIVE_MINUTES.value,
            TimeFrames.FIFTEEN_MINUTES.value,
            TimeFrames.THIRTY_MINUTES.value,
            TimeFrames.ONE_HOUR.value,
            TimeFrames.TWO_HOURS.value,
            TimeFrames.FOUR_HOURS.value,
            TimeFrames.SIX_HOURS.value,
            TimeFrames.TWELVE_HOURS.value,
            TimeFrames.ONE_DAY.value,
            TimeFrames.THREE_DAYS.value,
            TimeFrames.ONE_WEEK.value,
            TimeFrames.ONE_MONTH.value
        ))

    async def test_get_market_status(self):
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
            self.check_market_status_limits(
                market_status,
                low_cost_max=10, low_cost_min=1,    # no suitable /BTC pair for now
                has_price_limits=False
            )

    async def test_get_symbol_prices(self):
        # without limit
        symbol_prices = await self.get_symbol_prices()
        assert len(symbol_prices) == 50
        # check candles order (oldest first)
        self.ensure_elements_order(symbol_prices, PriceIndexes.IND_PRICE_TIME.value)
        # check last candle is the current candle
        assert symbol_prices[-1][PriceIndexes.IND_PRICE_TIME.value] >= self.get_time() - self.get_allowed_time_delta()

        # try with candles limit (used in candled updater)
        symbol_prices = await self.get_symbol_prices(limit=1500)
        # max candles is 1000
        assert len(symbol_prices) == 1000
        # check candles order (oldest first)
        self.ensure_elements_order(symbol_prices, PriceIndexes.IND_PRICE_TIME.value)
        # check last candle is the current candle
        assert symbol_prices[-1][PriceIndexes.IND_PRICE_TIME.value] >= self.get_time() - self.get_allowed_time_delta()

    async def test_get_historical_symbol_prices(self):
        # try with since and limit (used in data collector)
        for limit in (50, None):
            symbol_prices = await self.get_symbol_prices(since=self.CANDLE_SINCE, limit=limit)
            if limit:
                assert len(symbol_prices) == limit
            else:
                assert len(symbol_prices) > 5
            # check candles order (oldest first)
            self.ensure_elements_order(symbol_prices, PriceIndexes.IND_PRICE_TIME.value)
            # check that fetched candles are historical candles
            max_candle_time = self.get_time_after_time_frames(self.CANDLE_SINCE_SEC, len(symbol_prices))
            assert max_candle_time <= self.get_time()
            for candle in symbol_prices:
                assert self.CANDLE_SINCE_SEC <= candle[PriceIndexes.IND_PRICE_TIME.value] <= max_candle_time

    async def test_get_kline_price(self):
        kline_price = await self.get_kline_price()
        assert len(kline_price) == 1
        assert len(kline_price[0]) == 6
        kline_start_time = kline_price[0][PriceIndexes.IND_PRICE_TIME.value]
        # assert kline is the current candle
        assert kline_start_time >= self.get_time() - self.get_allowed_time_delta()

    async def test_get_order_book(self):
        order_book = await self.get_order_book()
        assert len(order_book[Ecobic.ASKS.value]) == 5
        assert len(order_book[Ecobic.ASKS.value][0]) == 2
        assert len(order_book[Ecobic.BIDS.value]) == 5
        assert len(order_book[Ecobic.BIDS.value][0]) == 2

    async def test_get_recent_trades(self):
        recent_trades = await self.get_recent_trades()
        assert len(recent_trades) == 50
        # check trades order (oldest first)
        self.ensure_elements_order(recent_trades, Ecoc.TIMESTAMP.value)

    async def test_get_price_ticker(self):
        # get_price_ticker is not support on spot market :
        # to be fixed in this exchange tentacle using create_ticker_from_kline
        with pytest.raises(octobot_trading.errors.FailedRequest):
            ticker = await self.get_price_ticker()
            # self._check_ticker(ticker, self.SYMBOL, check_content=True)

    async def test_get_all_currencies_price_ticker(self):
        # warning: fetches swap tickers
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
            assert ticker[Ectc.BID_VOLUME.value]
            assert ticker[Ectc.ASK.value]
            assert ticker[Ectc.ASK_VOLUME.value]
            assert ticker[Ectc.OPEN.value]
            assert ticker[Ectc.CLOSE.value]
            assert ticker[Ectc.LAST.value]
            assert ticker[Ectc.PREVIOUS_CLOSE.value]
            assert ticker[Ectc.BASE_VOLUME.value]
            assert ticker[Ectc.TIMESTAMP.value]
            RealExchangeTester.check_ticker_typing(ticker)
