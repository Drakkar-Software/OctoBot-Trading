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
import pytest_asyncio
import mock
import ccxt.async_support


import octobot_trading.exchanges as exchanges
import octobot_trading.enums as enums

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def basic_exchange_wrapper():
    async with exchanges.temporary_exchange_wrapper("binance", enums.ExchangeWrapperLibs.ASYNC_CCXT) as wrapper:
        return wrapper


async def test_constructor(basic_exchange_wrapper):
    assert isinstance(basic_exchange_wrapper.exchange, ccxt.async_support.binance)
    async with exchanges.temporary_exchange_wrapper("ftx", enums.ExchangeWrapperLibs.CCXT) as wrapper:
        assert isinstance(wrapper.exchange, ccxt.ftx)


async def test_temporary_exchange_wrapper():
    with mock.patch.object(ccxt.async_support.ftx, "close", mock.AsyncMock()) as close_mock:
        with pytest.raises(ZeroDivisionError):
            async with exchanges.temporary_exchange_wrapper("ftx", enums.ExchangeWrapperLibs.ASYNC_CCXT) as wrapper:
                assert isinstance(wrapper.exchange, ccxt.async_support.ftx)
                close_mock.assert_not_called()
                1/0
        close_mock.assert_called_once()


async def test_unsupported_lib():
    with pytest.raises(NotImplementedError):
        exchanges.BasicExchangeWrapper("binance", "plop")


async def test_get_available_time_frames(basic_exchange_wrapper):
    assert len(await basic_exchange_wrapper.get_available_time_frames()) > 10
    basic_exchange_wrapper.exchange.timeframes = ["1m"]
    assert await basic_exchange_wrapper.get_available_time_frames() == ["1m"]
