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
import octobot_trading.enums as enums
import octobot_trading.personal_data as personal_data
from octobot_trading.personal_data import SellLimitOrder, BuyLimitOrder

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


async def test__is_update_increasing_size(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator

    symbol_contract = DEFAULT_FUTURE_SYMBOL_CONTRACT
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=False)

    if not os.getenv('CYTHON_IGNORE'):
        # Closed
        position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
        assert position_inst._is_update_increasing_size(decimal.Decimal(-5))
        assert position_inst._is_update_increasing_size(decimal.Decimal(5))

        # LONG
        position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
        position_inst.update(update_size=decimal.Decimal(100))
        assert not position_inst._is_update_increasing_size(decimal.Decimal(-5))
        assert position_inst._is_update_increasing_size(decimal.Decimal(5))

        # SHORT
        position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
        position_inst.update(update_size=decimal.Decimal(-100))
        assert position_inst._is_update_increasing_size(decimal.Decimal(-5))
        assert not position_inst._is_update_increasing_size(decimal.Decimal(5))


async def test_get_quantity_to_close(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator

    position_inst = personal_data.LinearPosition(trader_inst, DEFAULT_FUTURE_SYMBOL_CONTRACT)
    quantity = decimal_random_quantity(1)
    position_inst.update(update_size=quantity)
    assert position_inst.get_quantity_to_close() == -quantity

    position_inst = personal_data.LinearPosition(trader_inst, DEFAULT_FUTURE_SYMBOL_CONTRACT)
    quantity = -decimal_random_quantity(1)
    position_inst.update(update_size=quantity)
    assert position_inst.get_quantity_to_close() == -quantity


async def test_update_size_from_order_with_long_one_way_position(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator

    symbol_contract = DEFAULT_FUTURE_SYMBOL_CONTRACT
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    position_inst.update(update_size=constants.ONE_HUNDRED)

    limit_sell = SellLimitOrder(trader_inst)
    limit_sell.update(order_type=enums.TraderOrderType.SELL_LIMIT,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=10,
                      quantity=decimal.Decimal(2),
                      price=20)
    assert position_inst.update_size_from_order(limit_sell) == (decimal.Decimal(-2), False)


async def test_update_size_from_order_with_long_close_position_one_way_position(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator
    symbol_contract = DEFAULT_FUTURE_SYMBOL_CONTRACT
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    position_inst.update(update_size=constants.ONE_HUNDRED)

    limit_sell = SellLimitOrder(trader_inst)
    limit_sell.update(order_type=enums.TraderOrderType.SELL_LIMIT,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=10,
                      quantity=decimal.Decimal(2),
                      price=20)
    limit_sell.close_position = True
    assert position_inst.update_size_from_order(limit_sell) == (-constants.ONE_HUNDRED, False)


async def test_update_size_from_order_with_long_reduce_only_one_way_position(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator
    symbol_contract = DEFAULT_FUTURE_SYMBOL_CONTRACT
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    position_inst.update(update_size=constants.ONE_HUNDRED)

    limit_sell = SellLimitOrder(trader_inst)
    limit_sell.update(order_type=enums.TraderOrderType.SELL_LIMIT,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=10,
                      quantity=constants.ONE_HUNDRED * constants.ONE_HUNDRED,
                      price=20)
    limit_sell.reduce_only = True
    assert position_inst.update_size_from_order(limit_sell) == (-constants.ONE_HUNDRED, False)

    # reduce only with closed position
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    position_inst.update(update_size=constants.ZERO)
    limit_sell = SellLimitOrder(trader_inst)
    limit_sell.update(order_type=enums.TraderOrderType.SELL_LIMIT,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=10,
                      quantity=constants.ONE_HUNDRED * constants.ONE_HUNDRED,
                      price=20)
    limit_sell.reduce_only = True
    assert position_inst.update_size_from_order(limit_sell) == (constants.ZERO, True)


async def test_update_size_from_order_with_long_oversold_one_way_position(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator
    symbol_contract = DEFAULT_FUTURE_SYMBOL_CONTRACT
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    position_inst.update(update_size=constants.ONE_HUNDRED)

    limit_sell = SellLimitOrder(trader_inst)
    limit_sell.update(order_type=enums.TraderOrderType.SELL_LIMIT,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=10,
                      quantity=constants.ONE_HUNDRED ** decimal.Decimal(5),
                      price=20)
    assert position_inst.update_size_from_order(limit_sell) == (-constants.ONE_HUNDRED ** decimal.Decimal(5), False)
    assert position_inst.size == decimal.Decimal("-9999999900")
    assert not position_inst.is_long()


async def test_update_size_from_order_with_short_one_way_position(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator
    symbol_contract = DEFAULT_FUTURE_SYMBOL_CONTRACT
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    position_inst.update(update_size=-constants.ONE_HUNDRED)

    buy_limit = BuyLimitOrder(trader_inst)
    buy_limit.update(order_type=enums.TraderOrderType.BUY_LIMIT,
                     symbol=DEFAULT_FUTURE_SYMBOL,
                     current_price=10,
                     quantity=decimal.Decimal(2),
                     price=20)
    assert position_inst.update_size_from_order(buy_limit) == (decimal.Decimal(2), False)


async def test_update_size_from_order_with_short_close_position_one_way_position(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator
    symbol_contract = DEFAULT_FUTURE_SYMBOL_CONTRACT
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    position_inst.update(update_size=-constants.ONE_HUNDRED)

    buy_limit = BuyLimitOrder(trader_inst)
    buy_limit.update(order_type=enums.TraderOrderType.BUY_LIMIT,
                     symbol=DEFAULT_FUTURE_SYMBOL,
                     current_price=10,
                     quantity=decimal.Decimal(2),
                     price=20)
    buy_limit.close_position = True
    assert position_inst.update_size_from_order(buy_limit) == (constants.ONE_HUNDRED, False)


async def test_update_size_from_order_with_short_reduce_only_one_way_position(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator
    symbol_contract = DEFAULT_FUTURE_SYMBOL_CONTRACT
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    position_inst.update(update_size=-constants.ONE_HUNDRED)

    buy_limit = BuyLimitOrder(trader_inst)
    buy_limit.update(order_type=enums.TraderOrderType.BUY_LIMIT,
                     symbol=DEFAULT_FUTURE_SYMBOL,
                     current_price=10,
                     quantity=constants.ONE_HUNDRED * constants.ONE_HUNDRED,
                     price=20)
    buy_limit.reduce_only = True
    assert position_inst.update_size_from_order(buy_limit) == (constants.ONE_HUNDRED, False)

    # reduce only with closed position
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    position_inst.update(update_size=constants.ZERO)
    buy_limit = BuyLimitOrder(trader_inst)
    buy_limit.update(order_type=enums.TraderOrderType.BUY_LIMIT,
                     symbol=DEFAULT_FUTURE_SYMBOL,
                     current_price=10,
                     quantity=constants.ONE_HUNDRED * constants.ONE_HUNDRED,
                     price=20)
    buy_limit.reduce_only = True
    assert position_inst.update_size_from_order(buy_limit) == (constants.ZERO, True)


async def test_update_size_from_order_with_short_overbought_one_way_position(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator
    symbol_contract = DEFAULT_FUTURE_SYMBOL_CONTRACT
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    position_inst.update(update_size=-constants.ONE_HUNDRED)

    buy_limit = BuyLimitOrder(trader_inst)
    buy_limit.update(order_type=enums.TraderOrderType.BUY_LIMIT,
                     symbol=DEFAULT_FUTURE_SYMBOL,
                     current_price=10,
                     quantity=constants.ONE_HUNDRED ** decimal.Decimal(5),
                     price=20)
    assert position_inst.update_size_from_order(buy_limit) == (constants.ONE_HUNDRED ** decimal.Decimal(5), False)
    assert position_inst.size == decimal.Decimal("9999999900")
    assert not position_inst.is_short()


async def test_update_size_from_order_with_long_oversold_hedge_position(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator
    symbol_contract = DEFAULT_FUTURE_SYMBOL_CONTRACT
    symbol_contract.set_position_mode(is_one_way=False)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    position_inst.update(update_size=constants.ONE_HUNDRED)

    limit_sell = SellLimitOrder(trader_inst)
    limit_sell.update(order_type=enums.TraderOrderType.SELL_LIMIT,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=10,
                      quantity=constants.ONE_HUNDRED ** decimal.Decimal(5),
                      price=20)
    # cannot switch side
    assert position_inst.update_size_from_order(limit_sell) == (-constants.ONE_HUNDRED, False)
    assert position_inst.size == constants.ZERO
    assert position_inst.is_idle()


async def test_update_size_from_order_with_short_overbought_hedge_position(future_trader_simulator):
    config, exchange_manager_inst, trader_inst = future_trader_simulator
    symbol_contract = DEFAULT_FUTURE_SYMBOL_CONTRACT
    symbol_contract.set_position_mode(is_one_way=False)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    position_inst.update(update_size=-constants.ONE_HUNDRED)

    buy_limit = BuyLimitOrder(trader_inst)
    buy_limit.update(order_type=enums.TraderOrderType.BUY_LIMIT,
                     symbol=DEFAULT_FUTURE_SYMBOL,
                     current_price=10,
                     quantity=constants.ONE_HUNDRED ** decimal.Decimal(5),
                     price=20)
    # cannot switch side
    assert position_inst.update_size_from_order(buy_limit) == (constants.ONE_HUNDRED, False)
    assert position_inst.size == constants.ZERO
    assert position_inst.is_idle()

