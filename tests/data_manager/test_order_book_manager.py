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

from octobot_trading.data_manager.order_book_manager import OrderBookManager
from tests.util.random_numbers import random_price_list, random_price, random_quantity

pytestmark = pytest.mark.asyncio


@pytest.fixture()
async def order_book_manager():
    ob_manager = OrderBookManager()
    await ob_manager.initialize()
    return ob_manager


async def test_init(order_book_manager):
    assert not order_book_manager.order_book_initialized
    assert order_book_manager.bids == []
    assert order_book_manager.asks == []
    assert order_book_manager.ask_quantity == 0
    assert order_book_manager.ask_price == 0
    assert order_book_manager.bid_quantity == 0
    assert order_book_manager.bid_price == 0


async def test_reset(order_book_manager):
    order_book_manager.bids = random_price_list(10)
    order_book_manager.bid_price = random_price()
    order_book_manager.bid_quantity = random_price()
    order_book_manager.reset_order_book()
    assert order_book_manager.bids == []
    assert order_book_manager.bid_quantity == 0
    assert order_book_manager.bid_price == 0


async def test_order_book_update(order_book_manager):
    r_price_1 = random_price_list(10)
    r_price_2 = random_price_list(10)
    r_price_3 = random_price_list(10)
    r_price_4 = random_price_list(10)
    order_book_manager.order_book_update(r_price_1, r_price_2)
    assert order_book_manager.order_book_initialized
    assert order_book_manager.asks == r_price_1
    assert order_book_manager.bids == r_price_2
    order_book_manager.order_book_update([], r_price_3)
    assert order_book_manager.asks == r_price_1
    assert order_book_manager.bids == r_price_3
    order_book_manager.order_book_update(r_price_4, [])
    assert order_book_manager.asks == r_price_4
    assert order_book_manager.bids == r_price_3
    order_book_manager.order_book_update([], [])
    assert order_book_manager.asks == r_price_4
    assert order_book_manager.bids == r_price_3


async def test_order_book_ticker_update(order_book_manager):
    b_price = random_price()
    a_price = random_price()
    b_quantity = random_quantity()
    a_quantity = random_quantity()
    order_book_manager.order_book_ticker_update(a_quantity, a_price, b_quantity, b_price)
    assert order_book_manager.ask_quantity == a_quantity
    assert order_book_manager.ask_price == a_price
    assert order_book_manager.bid_quantity == b_quantity
    assert order_book_manager.bid_price == b_price
