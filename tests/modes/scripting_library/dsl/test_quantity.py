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
import mock

import pytest

import octobot_trading.modes.scripting_library.dsl as dsl


def test_parse_quantity_types():
    assert dsl.parse_quantity(None) == (dsl.QuantityType.DELTA, None)
    assert dsl.parse_quantity(10) == (dsl.QuantityType.DELTA, decimal.Decimal(10))
    assert dsl.parse_quantity(-10) == (dsl.QuantityType.DELTA, decimal.Decimal(-10))
    assert dsl.parse_quantity(1.366666663347877) == (dsl.QuantityType.DELTA, decimal.Decimal("1.366666663347877"))
    assert dsl.parse_quantity("-10") == (dsl.QuantityType.DELTA, decimal.Decimal(-10))

    assert dsl.parse_quantity("%") == (dsl.QuantityType.PERCENT, None)
    assert dsl.parse_quantity("99.5%") == (dsl.QuantityType.PERCENT, decimal.Decimal("99.5"))
    assert dsl.parse_quantity("-0.11%") == (dsl.QuantityType.PERCENT, decimal.Decimal("-0.11"))

    assert dsl.parse_quantity("a%") == (dsl.QuantityType.AVAILABLE_PERCENT, None)
    assert dsl.parse_quantity("-0.11a%") == (dsl.QuantityType.AVAILABLE_PERCENT, decimal.Decimal("-0.11"))
    assert dsl.parse_quantity("%a-0.11") == (dsl.QuantityType.AVAILABLE_PERCENT, decimal.Decimal("-0.11"))

    assert dsl.parse_quantity("a") == (dsl.QuantityType.AVAILABLE, None)
    assert dsl.parse_quantity("-0.11a") == (dsl.QuantityType.AVAILABLE, decimal.Decimal("-0.11"))
    assert dsl.parse_quantity("a-0.11") == (dsl.QuantityType.AVAILABLE, decimal.Decimal("-0.11"))

    assert dsl.parse_quantity("e%") == (dsl.QuantityType.ENTRY_PERCENT, None)
    assert dsl.parse_quantity("-0.11e%") == (dsl.QuantityType.ENTRY_PERCENT, decimal.Decimal("-0.11"))
    assert dsl.parse_quantity("-0.11%e") == (dsl.QuantityType.ENTRY_PERCENT, decimal.Decimal("-0.11"))

    assert dsl.parse_quantity("e") == (dsl.QuantityType.ENTRY, None)
    assert dsl.parse_quantity("-0.11e") == (dsl.QuantityType.ENTRY, decimal.Decimal("-0.11"))
    assert dsl.parse_quantity("e-0.11") == (dsl.QuantityType.ENTRY, decimal.Decimal("-0.11"))

    assert dsl.parse_quantity("p%") == (dsl.QuantityType.POSITION_PERCENT, None)
    assert dsl.parse_quantity("-0.11p%") == (dsl.QuantityType.POSITION_PERCENT, decimal.Decimal("-0.11"))
    assert dsl.parse_quantity("%p-0.11") == (dsl.QuantityType.POSITION_PERCENT, decimal.Decimal("-0.11"))

    assert dsl.parse_quantity("p") == (dsl.QuantityType.POSITION, None)
    assert dsl.parse_quantity("-0.11p") == (dsl.QuantityType.POSITION, decimal.Decimal("-0.11"))
    assert dsl.parse_quantity("p-0.11") == (dsl.QuantityType.POSITION, decimal.Decimal("-0.11"))

    assert dsl.parse_quantity("@") == (dsl.QuantityType.FLAT, None)
    assert dsl.parse_quantity("-0.11@") == (dsl.QuantityType.FLAT, decimal.Decimal("-0.11"))
    assert dsl.parse_quantity("@-0.11") == (dsl.QuantityType.FLAT, decimal.Decimal("-0.11"))

    assert dsl.parse_quantity("wyz-0.11") == (dsl.QuantityType.UNKNOWN, None)
    assert dsl.parse_quantity("wyz12") == (dsl.QuantityType.UNKNOWN, None)
    assert dsl.parse_quantity("wyz") == (dsl.QuantityType.UNKNOWN, None)


def test_parse_quantity_edge_numbers():
    assert dsl.parse_quantity(0.000000001) == (dsl.QuantityType.DELTA, decimal.Decimal("0.000000001"))
    assert dsl.parse_quantity(100000000000000000000) \
           == (dsl.QuantityType.DELTA, decimal.Decimal("100000000000000000000"))
    assert dsl.parse_quantity("-1e-09e%") == (dsl.QuantityType.ENTRY_PERCENT, decimal.Decimal("-1e-09"))
    assert dsl.parse_quantity("1e09%e") == (dsl.QuantityType.ENTRY_PERCENT, decimal.Decimal("1e09"))
    assert dsl.parse_quantity("1e9e") == (dsl.QuantityType.ENTRY, decimal.Decimal("1e9"))
    with mock.patch.object(dsl.QuantityType, "parse", mock.Mock(return_value=(dsl.QuantityType.ENTRY, "e"))):
        with pytest.raises(RuntimeError):
            dsl.parse_quantity("0.000000001aa")
