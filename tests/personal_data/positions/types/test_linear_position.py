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

import pytest
import octobot_trading.constants as constants
import octobot_trading.personal_data as personal_data

from tests import event_loop
from tests.exchanges import future_simulated_exchange_manager
from tests.exchanges.traders import future_trader_simulator, DEFAULT_FUTURE_SYMBOL_CONTRACT, \
    DEFAULT_FUTURE_SYMBOL, DEFAULT_FUTURE_FUNDING_RATE
from tests.test_utils.random_numbers import decimal_random_price, decimal_random_quantity

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_update_value(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator
    position_inst = personal_data.LinearPosition(trader_inst, DEFAULT_FUTURE_SYMBOL_CONTRACT)
    position_inst.update(update_size=constants.ZERO)
    position_inst.update_value()
    assert position_inst.value == constants.ZERO
    position_inst.update(update_size=constants.ONE_HUNDRED)
    position_inst.update_value()
    assert position_inst.value == constants.ZERO
    position_inst.update(mark_price=constants.ONE_HUNDRED)
    position_inst.update_value()
    assert position_inst.value == decimal.Decimal("10000")


async def test_update_pnl(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator

    # long test
    position_inst = personal_data.LinearPosition(trader_inst, DEFAULT_FUTURE_SYMBOL_CONTRACT)
    position_inst.entry_price = constants.ONE_HUNDRED
    position_inst.update(update_size=constants.ONE_HUNDRED, mark_price=constants.ONE_HUNDRED)
    position_inst.update_pnl()
    assert position_inst.unrealised_pnl == constants.ZERO
    position_inst.update(update_size=constants.ONE_HUNDRED,
                               mark_price=decimal.Decimal(2) * constants.ONE_HUNDRED)
    position_inst.update_pnl()
    assert position_inst.unrealised_pnl == decimal.Decimal("20000")

    # short test
    position_inst = personal_data.LinearPosition(trader_inst, DEFAULT_FUTURE_SYMBOL_CONTRACT)
    position_inst.entry_price = constants.ONE_HUNDRED
    position_inst.update(update_size=-constants.ONE_HUNDRED, mark_price=constants.ONE_HUNDRED)
    position_inst.update_pnl()
    assert position_inst.unrealised_pnl == constants.ZERO
    position_inst.update(update_size=-constants.ONE_HUNDRED,
                               mark_price=constants.ONE_HUNDRED / decimal.Decimal(10))
    position_inst.update_pnl()
    assert position_inst.unrealised_pnl == decimal.Decimal("-18000")


async def test_update_initial_margin(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator
    position_inst = personal_data.LinearPosition(trader_inst, DEFAULT_FUTURE_SYMBOL_CONTRACT)

    position_inst.update(update_size=constants.ZERO, mark_price=constants.ZERO)
    position_inst.update_initial_margin()
    assert position_inst.initial_margin == constants.ZERO
    position_inst.update(update_size=constants.ONE_HUNDRED, mark_price=constants.ONE_HUNDRED)
    position_inst.update_initial_margin()
    assert position_inst.initial_margin == decimal.Decimal("10000")
    position_inst.leverage = constants.ONE_HUNDRED
    position_inst.update(update_size=constants.ONE_HUNDRED, mark_price=constants.ONE_HUNDRED)
    position_inst.update_initial_margin()
    assert position_inst.initial_margin == decimal.Decimal("200")


async def test_calculate_maintenance_margin(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator
    position_inst = personal_data.LinearPosition(trader_inst, DEFAULT_FUTURE_SYMBOL_CONTRACT)

    position_inst.symbol = DEFAULT_FUTURE_SYMBOL
    position_inst.update(update_size=constants.ZERO, mark_price=constants.ZERO)
    assert position_inst.calculate_maintenance_margin() == constants.ZERO
    position_inst.update(update_size=constants.ONE_HUNDRED, mark_price=constants.ONE_HUNDRED)
    assert position_inst.calculate_maintenance_margin() == constants.ZERO
    exchange_manager_inst.exchange_symbols_data.get_exchange_symbol_data(
        DEFAULT_FUTURE_SYMBOL).funding_manager.funding_rate = decimal.Decimal(DEFAULT_FUTURE_FUNDING_RATE)
    position_inst.update(update_size=constants.ONE_HUNDRED, mark_price=constants.ONE_HUNDRED)
    assert position_inst.calculate_maintenance_margin() == decimal.Decimal("0E-59")


async def test_update_isolated_liquidation_price(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator
    exchange_manager_inst.exchange_symbols_data.get_exchange_symbol_data(
        DEFAULT_FUTURE_SYMBOL).funding_manager.funding_rate = decimal.Decimal(DEFAULT_FUTURE_FUNDING_RATE)

    # long test
    position_inst = personal_data.LinearPosition(trader_inst, DEFAULT_FUTURE_SYMBOL_CONTRACT)
    position_inst.symbol = DEFAULT_FUTURE_SYMBOL
    position_inst.entry_price = constants.ONE_HUNDRED
    position_inst.update(update_size=constants.ONE_HUNDRED, mark_price=constants.ONE_HUNDRED)
    position_inst.update_isolated_liquidation_price()
    assert position_inst.liquidation_price == constants.ZERO
    position_inst.leverage = constants.ONE_HUNDRED
    position_inst.update(update_size=constants.ONE_HUNDRED,
                               mark_price=decimal.Decimal(2) * constants.ONE_HUNDRED)
    position_inst.update_isolated_liquidation_price()
    assert position_inst.liquidation_price == constants.ZERO

    # short test
    position_inst = personal_data.LinearPosition(trader_inst, DEFAULT_FUTURE_SYMBOL_CONTRACT)
    position_inst.symbol = DEFAULT_FUTURE_SYMBOL
    position_inst.entry_price = constants.ONE_HUNDRED
    position_inst.update(update_size=-constants.ONE_HUNDRED, mark_price=constants.ONE_HUNDRED)
    position_inst.update_isolated_liquidation_price()
    assert position_inst.liquidation_price == decimal.Decimal("10200.00000000000020816681712")
    position_inst.leverage = constants.ONE_HUNDRED
    position_inst.update(update_size=-constants.ONE_HUNDRED,
                               mark_price=constants.ONE_HUNDRED / decimal.Decimal(10))
    position_inst.update_isolated_liquidation_price()
    assert position_inst.liquidation_price == decimal.Decimal("20101.00000000000041633363423")


async def test_get_bankruptcy_price(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator

    # long test
    position_inst = personal_data.LinearPosition(trader_inst, DEFAULT_FUTURE_SYMBOL_CONTRACT)
    position_inst.entry_price = constants.ONE_HUNDRED
    position_inst.update(update_size=constants.ONE_HUNDRED, mark_price=constants.ONE_HUNDRED)
    assert position_inst.get_bankruptcy_price() == constants.ZERO
    assert position_inst.get_bankruptcy_price(with_mark_price=True) == constants.ONE_HUNDRED
    position_inst.leverage = constants.ONE_HUNDRED
    assert position_inst.get_bankruptcy_price() == decimal.Decimal("99.00")
    assert position_inst.get_bankruptcy_price(with_mark_price=True) == decimal.Decimal("100")
    position_inst.update(update_size=constants.ONE_HUNDRED,
                               mark_price=decimal.Decimal(2) * constants.ONE_HUNDRED)
    assert position_inst.get_bankruptcy_price() == decimal.Decimal("99.00")
    assert position_inst.get_bankruptcy_price(with_mark_price=True) == decimal.Decimal("200")

    # short test
    position_inst = personal_data.LinearPosition(trader_inst, DEFAULT_FUTURE_SYMBOL_CONTRACT)
    position_inst.entry_price = constants.ONE_HUNDRED
    position_inst.update(update_size=-constants.ONE_HUNDRED, mark_price=constants.ONE_HUNDRED)
    assert position_inst.get_bankruptcy_price() == decimal.Decimal("200")
    assert position_inst.get_bankruptcy_price(with_mark_price=True) == decimal.Decimal("100")
    position_inst.leverage = constants.ONE_HUNDRED
    assert position_inst.get_bankruptcy_price() == decimal.Decimal('101.00')
    assert position_inst.get_bankruptcy_price(with_mark_price=True) == decimal.Decimal('100')
    position_inst.update(update_size=-constants.ONE_HUNDRED,
                               mark_price=decimal.Decimal(2) * constants.ONE_HUNDRED)
    assert position_inst.get_bankruptcy_price() == constants.ZERO
    assert position_inst.get_bankruptcy_price(with_mark_price=True) == constants.ZERO


async def test_get_order_cost(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator
    position_inst = personal_data.LinearPosition(trader_inst, DEFAULT_FUTURE_SYMBOL_CONTRACT)

    position_inst.update(update_size=constants.ZERO, mark_price=constants.ZERO)
    assert position_inst.get_order_cost() == constants.ZERO
    position_inst.update(update_size=constants.ONE_HUNDRED, mark_price=constants.ONE_HUNDRED)
    assert position_inst.get_order_cost() == decimal.Decimal("10020.000")


async def test_get_fee_to_open(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator
    position_inst = personal_data.LinearPosition(trader_inst, DEFAULT_FUTURE_SYMBOL_CONTRACT)

    position_inst.update(update_size=constants.ZERO, mark_price=constants.ZERO)
    assert position_inst.get_fee_to_open() == constants.ZERO
    position_inst.update(update_size=constants.ONE_HUNDRED, mark_price=constants.ONE_HUNDRED)
    assert position_inst.get_fee_to_open() == decimal.Decimal("10.000")


async def test_update_fee_to_close(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator
    position_inst = personal_data.LinearPosition(trader_inst, DEFAULT_FUTURE_SYMBOL_CONTRACT)

    position_inst.update(update_size=constants.ZERO, mark_price=constants.ZERO)
    position_inst.update_fee_to_close()
    assert position_inst.fee_to_close == constants.ZERO
    position_inst.update(update_size=constants.ONE_HUNDRED, mark_price=constants.ONE_HUNDRED)
    position_inst.update_fee_to_close()
    assert position_inst.fee_to_close == decimal.Decimal("10")
