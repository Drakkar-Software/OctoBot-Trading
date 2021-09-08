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
import decimal
import os
import pytest
from asyncio import Event
from mock import patch, Mock

from tests.exchange_data import price_events_manager
from tests import event_loop
from tests.test_utils.random_numbers import random_recent_trade, decimal_random_price, random_price, random_timestamp

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_reset(price_events_manager):
    if not os.getenv('CYTHON_IGNORE'):
        price_events_manager.events.append(None)
        assert price_events_manager.events
        price_events_manager.reset()
        assert not price_events_manager.events


async def test_add_event(price_events_manager):
    price_events_manager.add_event(decimal_random_price(), random_timestamp(), True)
    price_events_manager.add_event(decimal_random_price(), random_timestamp(), False)
    if not os.getenv('CYTHON_IGNORE'):
        assert price_events_manager.events
        assert len(price_events_manager.events) == 2


async def test_handle_recent_trades(price_events_manager):
    random_price_1 = random_price(min_value=2)
    random_timestamp_1 = random_timestamp(min_value=2, max_value=1000)
    price_event_1 = price_events_manager.add_event(decimal.Decimal(str(random_price_1)), random_timestamp_1, True)
    with patch.object(price_event_1, 'set', new=Mock()) as price_event_1_set:
        price_events_manager.handle_recent_trades([])
        with pytest.raises(AssertionError):
            price_event_1_set.assert_called_once()
        price_events_manager.handle_recent_trades(
            [random_recent_trade(price=random_price(max_value=random_price_1 - 1),
                                 timestamp=random_timestamp(max_value=random_timestamp_1 - 1)),
             random_recent_trade(price=random_price(max_value=random_price_1 - 1),
                                 timestamp=random_timestamp(max_value=random_timestamp_1 - 1)),
             random_recent_trade(price=random_price(max_value=random_price_1 - 1),
                                 timestamp=random_timestamp(max_value=random_timestamp_1 - 1))])
        with pytest.raises(AssertionError):
            price_event_1_set.assert_called_once()
        price_events_manager.handle_recent_trades(
            [random_recent_trade(price=random_price(max_value=random_price_1 - 1)),
             random_recent_trade(price=random_price_1,
                                 timestamp=random_timestamp_1),
             random_recent_trade(price=random_price(max_value=random_price_1 - 1)),
             random_recent_trade(price=random_price(max_value=random_price_1 - 1))])
        price_event_1_set.assert_called_once()


async def test_handle_recent_trades_multiple_events(price_events_manager):
    random_price_1 = random_price(min_value=2)
    random_price_2 = random_price(min_value=random_price_1)
    random_timestamp_1 = random_timestamp(min_value=2, max_value=1000)
    random_timestamp_2 = random_timestamp(min_value=random_timestamp_1 + 2, max_value=5000)
    price_event_1 = price_events_manager.add_event(decimal.Decimal(str(random_price_1)), random_timestamp_1, True)
    price_event_2 = price_events_manager.add_event(decimal.Decimal(str(random_price_2)), random_timestamp_2, True)
    with patch.object(price_event_1, 'set', new=Mock()) as price_event_1_set, \
            patch.object(price_event_2, 'set', new=Mock()) as price_event_2_set:
        price_events_manager.handle_recent_trades(
            [random_recent_trade(price=random_price(max_value=random_price_1 - 1)),
             random_recent_trade(price=random_price(max_value=random_price_1 - 1)),
             random_recent_trade(price=random_price(max_value=random_price_1 - 1))])
        with pytest.raises(AssertionError):
            price_event_1_set.assert_called_once()
        with pytest.raises(AssertionError):
            price_event_2_set.assert_called_once()
        price_events_manager.handle_recent_trades(
            [random_recent_trade(price=random_price(max_value=random_price_1 - 1),
                                 timestamp=random_timestamp(max_value=random_timestamp_1 - 1)),
             random_recent_trade(price=random_price_2 - 1,
                                 timestamp=random_timestamp(min_value=random_timestamp_1,
                                                            max_value=random_timestamp_2))])
        price_event_1_set.assert_called_once()
        with pytest.raises(AssertionError):
            price_event_2_set.assert_called_once()
        price_events_manager.handle_recent_trades(
            [random_recent_trade(price=random_price(max_value=random_price_1 - 1)),
             random_recent_trade(price=random_price_2,
                                 timestamp=random_timestamp_2)])
        price_event_2_set.assert_called_once()

    price_event_1 = price_events_manager.add_event(decimal.Decimal(str(random_price_1)), random_timestamp_1, True)
    price_event_2 = price_events_manager.add_event(decimal.Decimal(str(random_price_2)), random_timestamp_2, True)
    with patch.object(price_event_1, 'set', new=Mock()) as price_event_1_set, \
            patch.object(price_event_2, 'set', new=Mock()) as price_event_2_set:
        price_events_manager.handle_recent_trades(
            [random_recent_trade(price=random_price(max_value=random_price_1 - 1),
                                 timestamp=random_timestamp(max_value=random_timestamp_1 - 1)),
             random_recent_trade(price=random_price_2 + 10,
                                 timestamp=random_timestamp(min_value=random_timestamp_2 + 1))])
        price_event_1_set.assert_called_once()
        price_event_2_set.assert_called_once()

    price_event_1 = price_events_manager.add_event(decimal.Decimal(str(random_price_1)), random_timestamp_1, True)
    price_event_2 = price_events_manager.add_event(decimal.Decimal(str(random_price_2)), random_timestamp_2, True)
    with patch.object(price_event_1, 'set', new=Mock()) as price_event_1_set, \
            patch.object(price_event_2, 'set', new=Mock()) as price_event_2_set:
        price_events_manager.handle_recent_trades(
            [random_recent_trade(price=random_price(min_value=random_price_1, max_value=random_price_2 - 1),
                                 timestamp=random_timestamp(min_value=random_timestamp_1 - 1)),
             random_recent_trade(price=random_price_2,
                                 timestamp=random_timestamp(max_value=random_timestamp_2 - 1))])
        price_event_1_set.assert_called_once()
        with pytest.raises(AssertionError):
            price_event_2_set.assert_called_once()


async def test_handle_price(price_events_manager):
    random_price_1 = random_price()
    random_timestamp_1 = random_timestamp(min_value=2, max_value=1000)
    price_event_1 = price_events_manager.add_event(decimal.Decimal(str(random_price_1)), random_timestamp_1, True)
    with patch.object(price_event_1, 'set', new=Mock()) as price_event_1_set:
        price_events_manager.handle_price(0, random_timestamp())
        with pytest.raises(AssertionError):
            price_event_1_set.assert_called_once()
        price_events_manager.handle_price(price=random_price(max_value=random_price_1 - 1),
                                          timestamp=random_timestamp())
        with pytest.raises(AssertionError):
            price_event_1_set.assert_called_once()
        price_events_manager.handle_price(price=random_price(max_value=random_price_1 - 1),
                                          timestamp=random_timestamp())
        price_events_manager.handle_price(price=random_price(min_value=random_price_1),
                                          timestamp=random_timestamp_1 - 1)
        with pytest.raises(AssertionError):
            price_event_1_set.assert_called_once()
        price_events_manager.handle_price(price=random_price(min_value=random_price_1),
                                          timestamp=random_timestamp_1 + 1)
        price_event_1_set.assert_called_once()


async def test_remove_event(price_events_manager):
    event_1 = price_events_manager.add_event(decimal_random_price(), random_timestamp(), True)
    event_2 = price_events_manager.add_event(decimal_random_price(), random_timestamp(), False)
    if not os.getenv('CYTHON_IGNORE'):
        assert price_events_manager.events
        price_events_manager.remove_event(event_1)
        assert event_1 not in price_events_manager.events
        assert len(price_events_manager.events) == 1
        price_events_manager.remove_event(Event())
        assert len(price_events_manager.events) == 1
        price_events_manager.remove_event(event_2)
        assert event_2 not in price_events_manager.events
        assert len(price_events_manager.events) == 0
