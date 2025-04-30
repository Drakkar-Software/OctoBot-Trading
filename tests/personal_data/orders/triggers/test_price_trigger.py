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
import decimal
import mock

import octobot_trading.personal_data as personal_data


@pytest.fixture
def mock_callback():
    return mock.AsyncMock()


@pytest.fixture
def trigger_price():
    return decimal.Decimal("100.0")


@pytest.fixture
def price_trigger(mock_callback, trigger_price):
    return personal_data.PriceTrigger(
        on_trigger_callback=mock_callback,
        on_trigger_callback_args=("arg1", "arg2"),
        trigger_price=trigger_price,
        trigger_above=True
    )


@pytest.mark.parametrize("current_price,trigger_above,expected", [
    (decimal.Decimal("101.0"), True, True),  # Above trigger price, trigger_above=True
    (decimal.Decimal("99.0"), True, False),  # Below trigger price, trigger_above=True
    (decimal.Decimal("100.0"), True, True),  # Equal trigger price, trigger_above=True
    (decimal.Decimal("101.0"), False, False),  # Above trigger price, trigger_above=False
    (decimal.Decimal("99.0"), False, True),  # Below trigger price, trigger_above=False
    (decimal.Decimal("100.0"), False, True),  # Equal trigger price, trigger_above=False
])
def test_triggers(current_price, trigger_above, expected, mock_callback, trigger_price):
    trigger = personal_data.PriceTrigger(mock_callback, ("arg1", "arg2"), trigger_price, trigger_above)
    assert trigger.triggers(current_price) == expected


def test_init(price_trigger, mock_callback, trigger_price):
    assert price_trigger.trigger_price == trigger_price
    assert price_trigger.trigger_above is True
    assert price_trigger.on_trigger_callback == mock_callback
    assert price_trigger.on_trigger_callback_args == ("arg1", "arg2")
    assert price_trigger._exchange_manager is None
    assert price_trigger._symbol is None


def test_update_from_other_trigger(price_trigger):
    other_trigger = personal_data.PriceTrigger(
        mock.AsyncMock(),
        ("other_arg",),
        decimal.Decimal("200.0"),
        False
    )

    price_trigger.update_from_other_trigger(other_trigger)
    assert price_trigger.trigger_price == decimal.Decimal("200.0")
    assert price_trigger.trigger_above is False
    # Original callback and args should remain unchanged
    assert price_trigger.on_trigger_callback_args == ("arg1", "arg2")


def test_str_representation(price_trigger):
    expected = (f"PriceTrigger({price_trigger.on_trigger_callback.__name__}): "
                f"trigger_price={price_trigger.trigger_price}, "
                f"trigger_above={price_trigger.trigger_above}")
    assert str(price_trigger) == expected


def test_clear_with_exchange_manager(price_trigger):
    # Setup mock exchange manager and related objects
    mock_price_events_manager = mock.Mock()
    mock_symbol_data = mock.Mock()
    mock_symbol_data.price_events_manager = mock_price_events_manager
    mock_exchange_symbols_data = mock.Mock()
    mock_exchange_symbols_data.get_exchange_symbol_data.return_value = mock_symbol_data
    mock_exchange_manager = mock.Mock()
    mock_exchange_manager.exchange_symbols_data = mock_exchange_symbols_data

    # Setup trigger with mock objects
    price_trigger._exchange_manager = mock_exchange_manager
    price_trigger._symbol = "BTC/USD"
    price_trigger._trigger_event = mock.Mock()

    # Call clear
    price_trigger.clear()

    # Verify that event was removed
    mock_price_events_manager.remove_event.assert_called_once_with(price_trigger._trigger_event)
    assert price_trigger._exchange_manager is None


def test_create_trigger_event(price_trigger):
    # Setup mock objects
    mock_price_events_manager = mock.Mock()
    mock_symbol_data = mock.Mock()
    mock_symbol_data.price_events_manager = mock_price_events_manager
    mock_exchange_symbols_data = mock.Mock()
    mock_exchange_symbols_data.get_exchange_symbol_data.return_value = mock_symbol_data
    mock_exchange_manager = mock.Mock()
    mock_exchange_manager.exchange_symbols_data = mock_exchange_symbols_data

    symbol = "BTC/USD"
    min_trigger_time = 1.0

    # Call create_trigger_event
    price_trigger._create_trigger_event(mock_exchange_manager, symbol, min_trigger_time)

    # Verify the event was created with correct parameters
    mock_price_events_manager.new_event.assert_called_once_with(
        price_trigger.trigger_price,
        min_trigger_time,
        price_trigger.trigger_above,
        False
    )
    assert price_trigger._exchange_manager == mock_exchange_manager
    assert price_trigger._symbol == symbol
