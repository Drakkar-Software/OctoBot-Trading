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
import mock
import decimal

import octobot_trading.modes.scripting_library.orders.offsets.offset as offset
import octobot_trading.modes.scripting_library.data.reading.exchange_public_data as exchange_public_data
import octobot_trading.modes.scripting_library.data.reading.exchange_private_data.open_positions as open_positions

from tests import event_loop
from tests.modes.scripting_library import null_context

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_get_offset(null_context):
    with mock.patch.object(exchange_public_data, "current_price", mock.AsyncMock(return_value=200)) \
            as current_price_mock:
        with mock.patch.object(offset, "parse_offset", mock.Mock(return_value=("", decimal.Decimal(10)))) \
                as parse_offset_mock:
            assert await offset.get_offset(null_context, 10) == decimal.Decimal(210)
            current_price_mock.assert_called_once_with(null_context)
            parse_offset_mock.assert_called_once_with(10)
            current_price_mock.reset_mock()

        with mock.patch.object(offset, "parse_offset", mock.Mock(return_value=("%", decimal.Decimal(-99)))):
            assert await offset.get_offset(null_context, 10) == decimal.Decimal(2)

        with mock.patch.object(offset, "parse_offset", mock.Mock(return_value=("%", decimal.Decimal(1000)))):
            assert await offset.get_offset(null_context, 10) == decimal.Decimal(2200)

    with mock.patch.object(open_positions, "average_open_pos_entry", mock.AsyncMock(return_value=500)) \
            as average_open_pos_entry_mock:
        with mock.patch.object(offset, "parse_offset", mock.Mock(return_value=("e%", decimal.Decimal(-50)))):
            assert await offset.get_offset(null_context, 10) == decimal.Decimal(250)
            average_open_pos_entry_mock.assert_called_once()

    with mock.patch.object(open_positions, "average_open_pos_entry", mock.AsyncMock(return_value=500)) \
            as average_open_pos_entry_mock:
        with mock.patch.object(offset, "parse_offset", mock.Mock(return_value=("e", decimal.Decimal(50)))):
            assert await offset.get_offset(null_context, 10) == decimal.Decimal(550)
            average_open_pos_entry_mock.assert_called_once()

    with mock.patch.object(offset, "parse_offset", mock.Mock(return_value=("@", decimal.Decimal(50)))):
        assert await offset.get_offset(null_context, 10) == decimal.Decimal(50)

    with mock.patch.object(offset, "parse_offset", mock.Mock(return_value=("@", decimal.Decimal(-50)))):
        with pytest.raises(RuntimeError):
            await offset.get_offset(null_context, 10)

    with mock.patch.object(offset, "parse_offset", mock.Mock(return_value=("XYZ", decimal.Decimal(-50)))):
        with pytest.raises(RuntimeError):
            await offset.get_offset(null_context, 10)


async def test_parse_offset():
    assert offset.parse_offset(10) == ("", decimal.Decimal(10))
    assert offset.parse_offset(-10) == ("", decimal.Decimal(-10))
    assert offset.parse_offset(1.366666663347877) == ("", decimal.Decimal("1.366666663347877"))
    assert offset.parse_offset("-10") == ("", decimal.Decimal(-10))

    assert offset.parse_offset("99.5%") == ("%", decimal.Decimal("99.5"))
    assert offset.parse_offset("-0.11%") == ("%", decimal.Decimal("-0.11"))

    assert offset.parse_offset("-0.11e%") == ("e%", decimal.Decimal("-0.11"))

    assert offset.parse_offset("-0.11e") == ("e", decimal.Decimal("-0.11"))
    assert offset.parse_offset("e-0.11") == ("e", decimal.Decimal("-0.11"))

    assert offset.parse_offset("-0.11@") == ("@", decimal.Decimal("-0.11"))
    assert offset.parse_offset("@-0.11") == ("@", decimal.Decimal("-0.11"))
