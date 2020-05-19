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
import asyncio

from tests.exchanges import backtesting_exchange_manager, backtesting_config, fake_backtesting
from octobot_trading.data_manager.prices_manager import PricesManager, calculate_mark_price_from_recent_trade_prices


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_initialize(backtesting_exchange_manager):
    prices_manager = PricesManager(backtesting_exchange_manager)
    assert prices_manager.mark_price == prices_manager.mark_price_set_time == 0
    assert not prices_manager.valid_price_received_event.is_set()

    # should be reset in init
    prices_manager.mark_price = 10
    prices_manager.mark_price_set_time = 10
    prices_manager.valid_price_received_event.set()

    await prices_manager.initialize_impl()
    assert prices_manager.mark_price == prices_manager.mark_price_set_time == 0
    assert not prices_manager.valid_price_received_event.is_set()


async def test_set_mark_price(backtesting_exchange_manager):
    prices_manager = PricesManager(backtesting_exchange_manager)
    prices_manager.set_mark_price(10)
    assert prices_manager.mark_price == 10
    assert prices_manager.mark_price_set_time == backtesting_exchange_manager.exchange.get_exchange_current_time()
    assert prices_manager.valid_price_received_event.is_set()


async def test_get_mark_price(backtesting_exchange_manager):
    prices_manager = PricesManager(backtesting_exchange_manager)
    # without a set price
    with pytest.raises(asyncio.TimeoutError):
        await prices_manager.get_mark_price(0.01)
    assert not prices_manager.valid_price_received_event.is_set()

    # set price
    prices_manager.set_mark_price(10)
    assert await prices_manager.get_mark_price(0.01) == 10
    assert prices_manager.valid_price_received_event.is_set()

    # expired price
    backtesting_exchange_manager.backtesting.time_manager.current_timestamp = 66666666
    with pytest.raises(asyncio.TimeoutError):
        await prices_manager.get_mark_price(0.01)
    assert not prices_manager.valid_price_received_event.is_set()

    # reset price with this time
    prices_manager.set_mark_price(10)
    assert await prices_manager.get_mark_price(0.01) == 10
    assert prices_manager.valid_price_received_event.is_set()

    # current time move within allowed range
    backtesting_exchange_manager.backtesting.time_manager.current_timestamp = 1
    assert await prices_manager.get_mark_price(0.01) == 10
    assert prices_manager.valid_price_received_event.is_set()

    # new value
    prices_manager.set_mark_price(42.0000172)
    assert await prices_manager.get_mark_price(0.01) == 42.0000172
    assert prices_manager.valid_price_received_event.is_set()


async def test_calculate_mark_price_from_recent_trade_prices():
    assert calculate_mark_price_from_recent_trade_prices([10, 5, 7]) == 7.333333333333333
    assert calculate_mark_price_from_recent_trade_prices([10, 20]) == 15
    assert calculate_mark_price_from_recent_trade_prices([]) == 0
