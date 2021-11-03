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
import octobot_trading.constants as constants
import octobot_trading.personal_data as personal_data

from tests import event_loop
from tests.exchanges import future_simulated_exchange_manager
from tests.exchanges.traders import future_trader_simulator, DEFAULT_FUTURE_SYMBOL_CONTRACT, DEFAULT_FUTURE_SYMBOL
from tests.test_utils.random_numbers import decimal_random_price, decimal_random_quantity

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_update_entry_price(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator

    position_inst = personal_data.LinearPosition(trader_inst, DEFAULT_FUTURE_SYMBOL_CONTRACT)

    assert position_inst.entry_price == constants.ZERO
    assert position_inst.mark_price == constants.ZERO

    mark_price = decimal_random_price(1)
    position_inst.update(mark_price=mark_price)
    assert position_inst.entry_price == mark_price
    assert position_inst.mark_price == mark_price


async def test_update_update_quantity(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator

    position_inst = personal_data.LinearPosition(trader_inst, DEFAULT_FUTURE_SYMBOL_CONTRACT)

    assert position_inst.quantity == constants.ZERO

    quantity = decimal_random_quantity(1)
    position_inst.update(update_size=quantity)
    assert position_inst.quantity == quantity


async def test__check_and_update_size_with_one_way_position_mode(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator

    symbol_contract = DEFAULT_FUTURE_SYMBOL_CONTRACT
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=True)

    if not os.getenv('CYTHON_IGNORE'):
        # LONG
        position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
        position_inst.update(update_size=decimal.Decimal(10))
        position_inst._check_and_update_size(decimal.Decimal(10))
        assert position_inst.size == decimal.Decimal(20)
        position_inst._check_and_update_size(decimal.Decimal(-10))
        assert position_inst.size == decimal.Decimal(10)
        position_inst._check_and_update_size(decimal.Decimal(-30))
        assert position_inst.size == decimal.Decimal(-20)

        # SHORT
        position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
        position_inst.update(update_size=decimal.Decimal(-100))
        position_inst._check_and_update_size(decimal.Decimal(-1.5))
        assert position_inst.size == decimal.Decimal(-101.5)
        position_inst._check_and_update_size(decimal.Decimal(51.5))
        assert position_inst.size == decimal.Decimal(-50)
        position_inst._check_and_update_size(decimal.Decimal(100))
        assert position_inst.size == decimal.Decimal(50)


async def test__check_and_update_size_with_hedge_position_mode(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator

    symbol_contract = DEFAULT_FUTURE_SYMBOL_CONTRACT
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=False)

    if not os.getenv('CYTHON_IGNORE'):
        # LONG
        position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
        position_inst.update(update_size=decimal.Decimal(100))
        position_inst._check_and_update_size(decimal.Decimal(-5))
        assert position_inst.size == decimal.Decimal(95)
        position_inst._check_and_update_size(decimal.Decimal("-66.481231232156215215874878"))
        assert position_inst.size == decimal.Decimal("28.518768767843784784125122")
        position_inst._check_and_update_size(decimal.Decimal(-450))
        assert position_inst.size == constants.ZERO  # position should is closed

        # SHORT
        position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
        position_inst.update(update_size=decimal.Decimal(-10))
        position_inst._check_and_update_size(decimal.Decimal(-10))
        assert position_inst.size == decimal.Decimal(-20)
        position_inst._check_and_update_size(decimal.Decimal(10))
        assert position_inst.size == decimal.Decimal(-10)
        position_inst._check_and_update_size(decimal.Decimal(50))
        assert position_inst.size == constants.ZERO  # position should is closed
