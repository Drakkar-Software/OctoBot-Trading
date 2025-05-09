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

import octobot_commons.constants as commons_constants
from octobot_commons.enums import TimeFrames, PriceIndexes
from octobot_trading.enums import ExchangeConstantsMarketStatusColumns as Ecmsc, \
    ExchangeConstantsOrderBookInfoColumns as Ecobic, ExchangeConstantsOrderColumns as Ecoc, \
    ExchangeConstantsTickersColumns as Ectc
import octobot_trading.errors as errors
import octobot_trading.exchanges.connectors.ccxt.constants as ccxt_constants
from tests_additional.real_exchanges.real_futures_exchange_tester import RealFuturesExchangeTester
# required to catch async loop context exceptions
from tests import event_loop

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


class TestKucoinFuturesRealExchangeTester(RealFuturesExchangeTester):
    EXCHANGE_NAME = "kucoinfutures"
    SYMBOL = "BTC/USDT:USDT"
    SYMBOL_2 = "BTC/USD:BTC"
    SYMBOL_3 = "XRP/USD:XRP"
    CANDLE_SINCE = 1722823200000    # Monday, August 5, 2024 2:00:00 AM
    CANDLE_SINCE_SEC = CANDLE_SINCE / 1000

    async def test_time_frames(self):
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
            TimeFrames.HEIGHT_HOURS.value,
            TimeFrames.TWELVE_HOURS.value,
            TimeFrames.ONE_DAY.value,
            TimeFrames.ONE_WEEK.value
        ))

    async def test_active_symbols(self):
        await self.inner_test_active_symbols(300, 300)

    async def test_get_market_status(self):
        for market_status in await self.get_market_statuses():
            self.ensure_required_market_status_values(market_status)
            # on this exchange, precision is a decimal instead of a number of digits
            assert 0 < market_status[Ecmsc.PRECISION.value][
                Ecmsc.PRECISION_AMOUNT.value] <= 1  # to be fixed in this exchange tentacle
            assert 0 < market_status[Ecmsc.PRECISION.value][
                Ecmsc.PRECISION_PRICE.value] <= 1  # to be fixed in this exchange tentacle
            assert all(elem in market_status[Ecmsc.LIMITS.value]
                       for elem in (Ecmsc.LIMITS_AMOUNT.value,
                                    Ecmsc.LIMITS_PRICE.value,
                                    Ecmsc.LIMITS_COST.value))
            # invalid values (should be much lower for XRP/BTC => remove price limit in tentacle
            self.check_market_status_limits(market_status,
                                            expect_invalid_price_limit_values=True,
                                            enable_price_and_cost_comparison=False)
            # ensure no "minFunds" in futures
            assert "minFunds" not in market_status[ccxt_constants.CCXT_INFO]

    async def test_get_symbol_prices(self):
        # without limit
        symbol_prices = await self.get_symbol_prices()
        assert len(symbol_prices) == 200
        # check candles order (oldest first)
        self.ensure_elements_order(symbol_prices, PriceIndexes.IND_PRICE_TIME.value)
        # check last candle is the current candle
        assert symbol_prices[-1][PriceIndexes.IND_PRICE_TIME.value] >= self.get_time() - self.get_allowed_time_delta()

        # try with candles limit (used in candled updater)
        symbol_prices = await self.get_symbol_prices(limit=100)
        assert len(symbol_prices) == 100
        # check candles order (oldest first)
        self.ensure_elements_order(symbol_prices, PriceIndexes.IND_PRICE_TIME.value)
        # check last candle is the current candle
        assert symbol_prices[-1][PriceIndexes.IND_PRICE_TIME.value] >= self.get_time() - self.get_allowed_time_delta()

    async def test_get_historical_symbol_prices(self):
        # try with since and limit (used in data collector)
        for limit in (50, None):
            assert len(await self.get_symbol_prices(since=self.CANDLE_SINCE, limit=limit)) == limit or 200
            # "to" param is required: add in tentacle
            symbol_prices = await self.get_symbol_prices(since=self.CANDLE_SINCE, limit=limit, to=self.get_ms_time())
            if limit:
                assert len(symbol_prices) == limit
                real_limit = int(
                    self.get_time_after_time_frames(self.CANDLE_SINCE_SEC, limit) * commons_constants.MSECONDS_TO_SECONDS
                )
                symbol_prices_real = await self.get_symbol_prices(since=self.CANDLE_SINCE, limit=limit, to=real_limit)
                assert symbol_prices_real == symbol_prices
            else:
                assert len(symbol_prices) > 5
            # check candles order (oldest first)
            self.ensure_elements_order(symbol_prices, PriceIndexes.IND_PRICE_TIME.value)
            # check that fetched candles are historical candles
            max_candle_time = self.get_time_after_time_frames(self.CANDLE_SINCE_SEC, len(symbol_prices))
            assert max_candle_time <= self.get_time()
            for candle in symbol_prices:
                assert self.CANDLE_SINCE_SEC <= candle[PriceIndexes.IND_PRICE_TIME.value] <= max_candle_time

    async def test_get_historical_ohlcv(self):
        await super().test_get_historical_ohlcv()

    async def test_get_kline_price(self):
        kline_price = await self.get_kline_price()
        assert len(kline_price) == 1
        assert len(kline_price[0]) == 6
        kline_start_time = kline_price[0][PriceIndexes.IND_PRICE_TIME.value]
        # assert kline is the current candle
        assert kline_start_time >= self.get_time() - self.get_allowed_time_delta()

    async def test_get_order_book(self):
        # kucoin requires a limit of None, 20 or 100 in order book
        order_book = await self.get_order_book(limit=20)
        assert 0 < order_book[Ecobic.TIMESTAMP.value] < self._get_ref_order_book_timestamp()
        assert len(order_book[Ecobic.ASKS.value]) == 20
        assert len(order_book[Ecobic.ASKS.value][0]) == 2
        assert len(order_book[Ecobic.BIDS.value]) == 20
        assert len(order_book[Ecobic.BIDS.value][0]) == 2
        
    async def test_get_order_books(self):
        # not supported
        await self.inner_test_unsupported_get_order_books()

    async def test_get_recent_trades(self):
        # note: on ccxt kucoin recent trades are received in reverse order from exchange and therefore should never be
        # filtered by limit before reversing (or most recent trades are lost)
        recent_trades = await self.get_recent_trades()
        assert len(recent_trades) == 50
        # check trades order (oldest first)
        self.ensure_elements_order(recent_trades, Ecoc.TIMESTAMP.value)

    async def test_get_price_ticker(self):
        ticker = await self.get_price_ticker()
        self._check_ticker(ticker, self.SYMBOL, check_content=True)

    async def test_get_all_currencies_price_ticker(self):
        tickers = await self.get_all_currencies_price_ticker()
        for symbol, ticker in tickers.items():
            self._check_ticker(ticker, symbol)

    async def test_get_funding_rate(self):
        funding_rate, ticker_funding_rate = await self.get_funding_rate()
        # patch NEXT_FUNDING_TIME & LAST_FUNDING_TIME in tentacle
        self._check_funding_rate(funding_rate, has_next_time_in_the_past=True, has_last_time=False)
        # no funding info in ticker
        self._check_funding_rate(ticker_funding_rate, has_rate=False, has_last_time=False,
                                 has_next_rate=False, has_next_time=False)

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
            assert ticker[Ectc.HIGH.value] is None
            assert ticker[Ectc.LOW.value] is None
            assert ticker[Ectc.BID.value]
            assert ticker[Ectc.BID_VOLUME.value]
            assert ticker[Ectc.ASK.value]
            assert ticker[Ectc.ASK_VOLUME.value]
            assert ticker[Ectc.OPEN.value] is None
            assert ticker[Ectc.CLOSE.value]
            assert ticker[Ectc.LAST.value]
            assert ticker[Ectc.PREVIOUS_CLOSE.value] is None
            assert ticker[Ectc.BASE_VOLUME.value] is None
            assert ticker[Ectc.TIMESTAMP.value]
            RealFuturesExchangeTester.check_ticker_typing(
                ticker,
                check_open=False, check_low=False, check_high=False, check_base_volume=False
            )
