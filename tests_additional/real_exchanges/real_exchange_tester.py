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
from ccxt import Exchange

from octobot_commons.constants import MINUTE_TO_SECONDS, MSECONDS_TO_SECONDS
from octobot_commons.enums import TimeFrames, TimeFramesMinutes
from tests_additional.real_exchanges import get_exchange_manager


class RealExchangeTester:
    # enter exchange name as a class variable here
    EXCHANGE_NAME = None
    SYMBOL = None
    # default is 1h, change if necessary
    TIME_FRAME = TimeFrames.ONE_HOUR

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

    async def time_frames(self):
        async with get_exchange_manager(self.EXCHANGE_NAME) as exchange_manager:
            return exchange_manager.exchange.client.timeframes

    async def get_market_status(self):
        async with get_exchange_manager(self.EXCHANGE_NAME) as exchange_manager:
            return exchange_manager.exchange.get_market_status(self.SYMBOL)

    async def get_symbol_prices(self):
        async with get_exchange_manager(self.EXCHANGE_NAME) as exchange_manager:
            return await exchange_manager.exchange.get_symbol_prices(self.SYMBOL, self.TIME_FRAME)

    async def get_kline_price(self):
        async with get_exchange_manager(self.EXCHANGE_NAME) as exchange_manager:
            return await exchange_manager.exchange.get_kline_price(self.SYMBOL, self.TIME_FRAME)

    async def get_order_book(self, **kwargs):
        async with get_exchange_manager(self.EXCHANGE_NAME) as exchange_manager:
            return await exchange_manager.exchange.get_order_book(self.SYMBOL, **kwargs)

    async def get_recent_trades(self):
        async with get_exchange_manager(self.EXCHANGE_NAME) as exchange_manager:
            return await exchange_manager.exchange.get_recent_trades(self.SYMBOL)

    async def get_price_ticker(self):
        async with get_exchange_manager(self.EXCHANGE_NAME) as exchange_manager:
            return await exchange_manager.exchange.get_price_ticker(self.SYMBOL)

    async def get_all_currencies_price_ticker(self):
        async with get_exchange_manager(self.EXCHANGE_NAME) as exchange_manager:
            return await exchange_manager.exchange.get_all_currencies_price_ticker()

    def get_allowed_time_delta(self):
        return TimeFramesMinutes[self.TIME_FRAME] * MINUTE_TO_SECONDS * MSECONDS_TO_SECONDS * 1.3

    @staticmethod
    def get_time():
        return Exchange.milliseconds()

    @staticmethod
    def ensure_elements_order(elements, sort_key, reverse=False):
        assert sorted(elements, key=lambda x: x[sort_key], reverse=reverse) == elements
