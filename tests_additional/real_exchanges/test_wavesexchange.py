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
from tests_additional.real_exchanges.real_exchange_tester import RealExchangeTester
import octobot_trading.exchanges as exchanges
import octobot_trading.errors as errors
# required to catch async loop context exceptions
from tests import event_loop

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


class TestWavesExchangeRealExchangeTester(RealExchangeTester):
    EXCHANGE_NAME = "wavesexchange"
    SYMBOL = "ETH/USDT"
    SYMBOL_2 = "CRO/XTN"
    SYMBOL_3 = "SHIB/XTN"
    ALLOWED_TIMEFRAMES_WITHOUT_CANDLE = RealExchangeTester.ALLOWED_TIMEFRAMES_WITHOUT_CANDLE + 1    # account for dumped candle

    async def test_time_frames(self):
        time_frames = await self.time_frames()
        assert all(time_frame in time_frames for time_frame in (
            TimeFrames.ONE_MINUTE.value,
            TimeFrames.FIVE_MINUTES.value,
            TimeFrames.FIFTEEN_MINUTES.value,
            TimeFrames.THIRTY_MINUTES.value,
            TimeFrames.ONE_HOUR.value,
            TimeFrames.TWO_HOURS.value,
            TimeFrames.FOUR_HOURS.value,
            TimeFrames.SIX_HOURS.value,
            TimeFrames.TWELVE_HOURS.value,
            TimeFrames.ONE_DAY.value,
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
            self.check_market_status_limits(market_status, has_price_limits=False)

    async def test_get_symbol_prices(self):
        previous_DUMP_INCOMPLETE_LAST_CANDLE_value = exchanges.RestExchange.DUMP_INCOMPLETE_LAST_CANDLE
        try:
            # todo set RestExchange.DUMP_INCOMPLETE_LAST_CANDLE = True in exchange tentacle
            exchanges.RestExchange.DUMP_INCOMPLETE_LAST_CANDLE = True
            # without limit
            # broken because last X candles have None prices (raising TypeError)
            with pytest.raises(errors.UnexpectedAdapterError):
                symbol_prices = await self.get_symbol_prices()
            return
            assert len(symbol_prices) == 1440 - 1 or len(symbol_prices) == 1440  # last candle might be removed
            # check candles order (oldest first)
            self.ensure_elements_order(symbol_prices, PriceIndexes.IND_PRICE_TIME.value)
            # check last candle is the current candle
            assert symbol_prices[-1][PriceIndexes.IND_PRICE_TIME.value] >= self.get_time() - self.get_allowed_time_delta()

            # try with candles limit (used in candled updater)
            symbol_prices = await self.get_symbol_prices(limit=201)
            assert len(symbol_prices) == 200 or len(symbol_prices) == 201  # last candle might be removed
            # check candles order (oldest first)
            self.ensure_elements_order(symbol_prices, PriceIndexes.IND_PRICE_TIME.value)
            # check last candle is the current candle
            assert symbol_prices[-1][PriceIndexes.IND_PRICE_TIME.value] >= self.get_time() - self.get_allowed_time_delta()

            with pytest.raises(errors.UnexpectedAdapterError):
                # try with since and limit (used in data collector)
                assert await self.get_symbol_prices(since=self.CANDLE_SINCE, limit=50) == []    # not supported
        finally:
            exchanges.RestExchange.DUMP_INCOMPLETE_LAST_CANDLE = previous_DUMP_INCOMPLETE_LAST_CANDLE_value

    async def test_get_kline_price(self):
        previous_DUMP_INCOMPLETE_LAST_CANDLE_value = exchanges.RestExchange.DUMP_INCOMPLETE_LAST_CANDLE
        try:
            exchanges.RestExchange.DUMP_INCOMPLETE_LAST_CANDLE = True
            # not supported because of exchanges.RestExchange.DUMP_INCOMPLETE_LAST_CANDLE
            with pytest.raises(errors.NotSupported):
                kline_price = await self.get_kline_price(limit=2)
                assert len(kline_price) == 1
                assert len(kline_price[0]) == 6
                kline_start_time = kline_price[0][PriceIndexes.IND_PRICE_TIME.value]
                # assert kline is the current candle
                assert kline_start_time >= self.get_time() - self.get_allowed_time_delta()
        finally:
            exchanges.RestExchange.DUMP_INCOMPLETE_LAST_CANDLE = previous_DUMP_INCOMPLETE_LAST_CANDLE_value

    async def test_get_order_book(self):
        order_book = await self.get_order_book()
        assert len(order_book[Ecobic.ASKS.value]) == 6
        assert len(order_book[Ecobic.ASKS.value][0]) == 2
        assert len(order_book[Ecobic.BIDS.value]) == 6
        assert len(order_book[Ecobic.BIDS.value][0]) == 2

    async def test_get_recent_trades(self):
        recent_trades = await self.get_recent_trades()
        assert len(recent_trades) == 50
        # check trades order (oldest first)
        self.ensure_elements_order(recent_trades, Ecoc.TIMESTAMP.value)

    async def test_get_price_ticker(self):
        ticker = await self.get_price_ticker()
        self._check_ticker(ticker, self.SYMBOL, check_content=True)

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
            assert ticker[Ectc.BID.value] is None
            assert ticker[Ectc.BID_VOLUME.value] is None
            assert ticker[Ectc.ASK.value] is None
            assert ticker[Ectc.ASK_VOLUME.value] is None
            assert ticker[Ectc.OPEN.value]
            assert ticker[Ectc.CLOSE.value]
            assert ticker[Ectc.LAST.value]
            assert ticker[Ectc.PREVIOUS_CLOSE.value] is None
            assert ticker[Ectc.BASE_VOLUME.value]
            assert ticker[Ectc.TIMESTAMP.value] is None  # will trigger an 'Ignored incomplete ticker'
            RealExchangeTester.check_ticker_typing(ticker, check_timestamp=False)
