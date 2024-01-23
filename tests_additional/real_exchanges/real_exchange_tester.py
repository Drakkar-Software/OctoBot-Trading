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
import contextlib

import ccxt.async_support
from ccxt import Exchange

import octobot_commons.constants as constants
import octobot_commons.enums as commons_enums
import octobot_trading.enums as trading_enums
import octobot_trading.exchanges.connectors.ccxt.ccxt_client_util as ccxt_client_util
import octobot_trading.exchanges.util as exchanges_util
from octobot_trading.enums import ExchangeConstantsTickersColumns as Ectc, \
    ExchangeConstantsMarketStatusColumns as Ecmsc
from tests_additional.real_exchanges import get_exchange_manager


class RealExchangeTester:
    # enter exchange name as a class variable here
    EXCHANGE_NAME = None
    EXCHANGE_TYPE = trading_enums.ExchangeTypes.SPOT.value
    SYMBOL = None
    SYMBOL_2 = None
    SYMBOL_3 = None
    # default is 1h, change if necessary
    TIME_FRAME = commons_enums.TimeFrames.ONE_HOUR
    ALLOWED_TIMEFRAMES_WITHOUT_CANDLE = 0
    CANDLE_SINCE = 1661990400000  # 1 September 2022 00:00:00
    CANDLE_SINCE_SEC = CANDLE_SINCE / 1000
    REQUIRES_AUTH = False  # set True when even normally public apis require authentication
    MARKET_STATUS_TYPE = trading_enums.ExchangeTypes.SPOT.value
    HISTORICAL_CANDLES_TO_FETCH_COUNT = 650

    # Public methods: to be implemented as tests
    # Use await self._[method_name] to get the test request result
    # ex: market_status = await self.get_market_status()

    # unauthenticated API
    async def test_time_frames(self):
        pass

    async def test_get_market_status(self):
        pass

    async def test_get_symbol_prices(self):
        pass

    async def test_get_historical_symbol_prices(self):
        pass

    async def test_get_kline_price(self):
        pass

    async def test_get_order_book(self):
        pass

    async def test_get_recent_trades(self):
        pass

    async def test_get_price_ticker(self):
        pass

    async def test_get_all_currencies_price_ticker(self):
        pass

    # authenticated API
    # TODO
    # async def test_get_balance(self):
    #     pass
    #
    # async def test_get_order(self):
    #     pass
    #
    # async def test_get_all_orders(self):
    #     pass
    #
    # async def test_get_open_orders(self):
    #     pass
    #
    # async def test_get_closed_orders(self):
    #     pass
    #
    # async def test_get_my_recent_trades(self):
    #     pass
    #
    # async def test_cancel_order(self):
    #     pass
    #
    # async def test_create_order(self):
    #     pass

    async def test_get_historical_ohlcv(self):
        # common implementation, should always work if candles history is supported
        historical_ohlcv = await self.get_historical_ohlcv()
        assert len(historical_ohlcv) > 500  # should be around 650
        self.ensure_elements_order(historical_ohlcv, commons_enums.PriceIndexes.IND_PRICE_TIME.value)
        self.ensure_unique_elements(historical_ohlcv, commons_enums.PriceIndexes.IND_PRICE_TIME.value)
        start, end = self.get_historical_ohlcv_start_and_end_times()
        max_candle_time = self.get_time_after_time_frames(start, len(historical_ohlcv))
        assert max_candle_time <= end
        assert max_candle_time <= self.get_time()
        # on some exchanges, a lot of candles are missing, ensure more than 1 fetch succeeded
        assert (
            self.HISTORICAL_CANDLES_TO_FETCH_COUNT * 0.85
            < len(historical_ohlcv)
            <= self.HISTORICAL_CANDLES_TO_FETCH_COUNT
        )
        for candle in historical_ohlcv:
            assert start <= candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value] <= end

    def get_config(self):
        return {
            constants.CONFIG_EXCHANGES: {
                self.EXCHANGE_NAME: {
                    constants.CONFIG_EXCHANGE_TYPE: self.EXCHANGE_TYPE
                }
            }
        }

    @contextlib.asynccontextmanager
    async def get_exchange_manager(self, market_filter=None):
        async with get_exchange_manager(
            self.EXCHANGE_NAME, config=self.get_config(),
            authenticated=self.REQUIRES_AUTH, market_filter=market_filter
        ) as exchange_manager:
            yield exchange_manager

    async def time_frames(self):
        async with self.get_exchange_manager() as exchange_manager:
            return exchange_manager.exchange.time_frames

    async def get_market_statuses(self):
        # return 2 different market status with different traded pairs to reduce possible
        # side effects using only one pair.
        async with self.get_exchange_manager() as exchange_manager:
            self._ensure_market_status_cachability(exchange_manager)
            return exchange_manager.exchange.get_market_status(self.SYMBOL), \
                exchange_manager.exchange.get_market_status(self.SYMBOL_2), \
                exchange_manager.exchange.get_market_status(self.SYMBOL_3)

    def _ensure_market_status_cachability(self, exchange_manager):
        client_using_cached_markets = getattr(ccxt.async_support, self.EXCHANGE_NAME)()
        ccxt_client_util.load_markets_from_cache(client_using_cached_markets)
        assert exchange_manager.exchange.connector.client.markets == client_using_cached_markets.markets

    async def get_symbol_prices(self, limit=None, **kwargs):
        async with self.get_exchange_manager() as exchange_manager:
            return await exchange_manager.exchange.get_symbol_prices(self.SYMBOL, self.TIME_FRAME,
                                                                     limit=limit, **kwargs)

    async def get_historical_ohlcv(self, **kwargs) -> list:
        async with self.get_exchange_manager() as exchange_manager:
            start, end = self.get_historical_ohlcv_start_and_end_times()
            start_ms, end_ms = start * 1000, end * 1000
            ohlcvs = []
            async for ohlcv in exchanges_util.get_historical_ohlcv(
                exchange_manager, self.SYMBOL, self.TIME_FRAME, start_ms, end_ms, request_retry_timeout=2, **kwargs
            ):
                ohlcvs.extend(ohlcv)
            return ohlcvs

    def get_historical_ohlcv_start_and_end_times(self):
        start = self.get_time() - (self.get_timeframe_seconds() * self.HISTORICAL_CANDLES_TO_FETCH_COUNT * 2)
        end = self.get_time_after_time_frames(start, self.HISTORICAL_CANDLES_TO_FETCH_COUNT)
        return start, end

    async def get_kline_price(self, **kwargs):
        async with self.get_exchange_manager() as exchange_manager:
            return await exchange_manager.exchange.get_kline_price(self.SYMBOL, self.TIME_FRAME, **kwargs)

    async def get_order_book(self, **kwargs):
        async with self.get_exchange_manager() as exchange_manager:
            return await exchange_manager.exchange.get_order_book(self.SYMBOL, **kwargs)

    async def get_recent_trades(self, limit=50):
        async with self.get_exchange_manager() as exchange_manager:
            return await exchange_manager.exchange.get_recent_trades(self.SYMBOL, limit=limit)

    async def get_price_ticker(self):
        async with self.get_exchange_manager() as exchange_manager:
            return await exchange_manager.exchange.get_price_ticker(self.SYMBOL)

    async def get_all_currencies_price_ticker(self, market_filter=None, **kwargs):
        async with self.get_exchange_manager(market_filter=market_filter) as exchange_manager:
            return await exchange_manager.exchange.get_all_currencies_price_ticker(**kwargs)

    def get_market_filter(self):
        def market_filter(market):
            return (
                market[trading_enums.ExchangeConstantsMarketStatusColumns.SYMBOL.value]
                in (self.SYMBOL, self.SYMBOL_2)
            )

        return market_filter

    def get_allowed_time_delta(self):
        return (self.ALLOWED_TIMEFRAMES_WITHOUT_CANDLE + 1) * \
            commons_enums.TimeFramesMinutes[self.TIME_FRAME] * \
            constants.MINUTE_TO_SECONDS * 1.3

    @staticmethod
    def get_time():
        return Exchange.seconds()

    @staticmethod
    def get_ms_time():
        return int(Exchange.milliseconds())

    def get_timeframe_seconds(self):
        return commons_enums.TimeFramesMinutes[self.TIME_FRAME] * constants.MINUTE_TO_SECONDS

    def get_time_after_time_frames(self, start, time_frames_count):
        return start + self.get_timeframe_seconds() * time_frames_count

    def get_timeframe_ms_delta(self, time_frames_count):
        return self.get_ms_time() - (self.get_timeframe_seconds() * time_frames_count * constants.MSECONDS_TO_SECONDS)

    @staticmethod
    def ensure_elements_order(elements, sort_key, reverse=False):
        assert sorted(elements, key=lambda x: x[sort_key], reverse=reverse) == elements

    @staticmethod
    def ensure_unique_elements(elements, key):
        assert len(elements) == len(set(element[key] for element in elements))

    def check_market_status_limits(self, market_status,
                                   normal_price_max=10000, normal_price_min=1e-06,
                                   normal_cost_max=10000, normal_cost_min=1e-06,
                                   low_price_max=1e-07, low_price_min=1e-09,
                                   low_cost_max=1e-03, low_cost_min=1e-06,
                                   expect_invalid_price_limit_values=False,
                                   expect_inferior_or_equal_price_and_cost=False,
                                   enable_price_and_cost_comparison=True,
                                   has_price_limits=True):
        min_price = market_status[Ecmsc.LIMITS.value][Ecmsc.LIMITS_PRICE.value][Ecmsc.LIMITS_PRICE_MIN.value]
        max_price = market_status[Ecmsc.LIMITS.value][Ecmsc.LIMITS_PRICE.value][Ecmsc.LIMITS_PRICE_MAX.value]
        min_cost = market_status[Ecmsc.LIMITS.value][Ecmsc.LIMITS_COST.value][Ecmsc.LIMITS_COST_MIN.value]
        has_min_or_max_price = min_price not in (None, 0) or max_price not in (None, 0)
        if has_min_or_max_price and not has_price_limits:
            raise AssertionError(
                f"Expect no price limit values but min or max price limit is set (min: {min_price} max: {max_price})"
            )
        if not has_min_or_max_price and has_price_limits:
            raise AssertionError(
                f"Expect price limit values but min or max price limit is not set (min: {min_price} max: {max_price})"
            )
        has_price_limit_value = min_price not in (None, 0)
        has_cost_limit_value = min_cost not in (None, 0)
        has_limit_value = has_price_limit_value and has_cost_limit_value
        if (not has_limit_value) and expect_invalid_price_limit_values:
            raise AssertionError("No price and limit value does not mean invalid values")
        if not expect_invalid_price_limit_values and market_status[Ecmsc.SYMBOL.value] == self.SYMBOL_3:
            # if these test are not passing, it means that limits are invalid
            # (limits should be much lower for SYMBOL_3 which is the low price pair, ex: XRP/BTC)
            # => set expect_invalid_price_limit_values to True in call and
            # remove price limit in exchange tentacle market status fixer if this is the case
            if has_price_limit_value:
                assert (not has_price_limit_value) or low_price_max >= min_price >= low_price_min
            assert (not has_cost_limit_value) or low_cost_max >= min_cost >= low_cost_min
        else:
            if has_price_limit_value:
                assert (not has_price_limit_value) or normal_price_max >= min_price >= normal_price_min
            assert (not has_cost_limit_value) or normal_cost_max >= min_cost >= normal_cost_min
        if has_price_limits and enable_price_and_cost_comparison and has_limit_value:
            # Consistency here is not required by OctoBot. Fix in tentacles if consistency
            # in price/cost comparison becomes required and min_price <= min_cost is false without a good reason
            if expect_inferior_or_equal_price_and_cost:
                assert min_price >= min_cost
            else:
                assert min_price <= min_cost

    @staticmethod
    def check_ticker_typing(ticker, check_open=True, check_high=True, check_low=True,
                            check_close=True, check_base_volume=True, check_timestamp=True):
        if check_open:
            assert isinstance(ticker[Ectc.OPEN.value], (float, int))
        if check_high:
            assert isinstance(ticker[Ectc.HIGH.value], (float, int))
        if check_low:
            assert isinstance(ticker[Ectc.LOW.value], (float, int))
        if check_close:
            assert isinstance(ticker[Ectc.CLOSE.value], (float, int))
        if check_base_volume:
            assert isinstance(ticker[Ectc.BASE_VOLUME.value], (float, int))
        if check_timestamp:
            assert isinstance(ticker[Ectc.TIMESTAMP.value], (float, int))
