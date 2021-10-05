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
import octobot_trading.constants as constants
import octobot_trading.personal_data as personal_data

from tests import event_loop
from tests.exchanges import future_simulated_exchange_manager
from tests.exchanges.traders import future_trader_simulator
from tests.exchanges.traders import future_trader
from tests.test_utils.random_numbers import decimal_random_price, decimal_random_quantity

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_update_entry_price(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator

    position_inst = personal_data.Position(trader_inst)

    assert position_inst.entry_price == constants.ZERO
    assert position_inst.mark_price == constants.ZERO

    mark_price = decimal_random_price(1)
    await position_inst.update(mark_price=mark_price)
    assert position_inst.entry_price == mark_price
    assert position_inst.mark_price == mark_price


async def test_update_update_quantity(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator

    position_inst = personal_data.LinearPosition(trader_inst)

    assert position_inst.quantity == constants.ZERO

    quantity = decimal_random_quantity(1)
    await position_inst.update(update_quantity=quantity)
    assert position_inst.quantity == quantity
