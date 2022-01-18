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
from mock import mock

import octobot_trading.constants as constants
import octobot_trading.enums as enums
import octobot_trading.personal_data as personal_data
from octobot_trading.personal_data import SellLimitOrder, BuyLimitOrder, BuyMarketOrder, SellMarketOrder

from tests import event_loop
from tests.exchanges import future_simulated_exchange_manager
from tests.exchanges.traders import future_trader_simulator_with_default_linear, DEFAULT_FUTURE_SYMBOL
from tests.test_utils.random_numbers import decimal_random_price, decimal_random_quantity

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_update_entry_price(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear

    position_inst = personal_data.LinearPosition(trader_inst, default_contract)

    assert position_inst.entry_price == constants.ZERO
    assert position_inst.mark_price == constants.ZERO

    mark_price = decimal_random_price(constants.ONE)
    await position_inst.update(mark_price=mark_price, update_size=constants.ONE)
    assert position_inst.entry_price == mark_price
    assert position_inst.mark_price == mark_price


async def test_update_entry_price_when_switching_side_on_one_way(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear

    symbol_contract = default_contract
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=True)
    await position_inst.initialize()
    position_inst.update_from_raw(
        {
            enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL
        }
    )

    mark_price = decimal.Decimal(80)
    await position_inst.update(mark_price=mark_price, update_size=decimal.Decimal(0.01))
    assert position_inst.entry_price == mark_price
    assert position_inst.mark_price == mark_price

    # updating mark price
    await position_inst.update(mark_price=decimal.Decimal(90))
    assert position_inst.is_long()

    # switching long to short with new mark price
    mark_price = decimal.Decimal(100)
    await position_inst.update(mark_price=mark_price, update_size=-decimal.Decimal(0.02))
    assert position_inst.is_short()
    assert position_inst.mark_price == mark_price
    assert position_inst.entry_price == mark_price

    # updating mark price
    await position_inst.update(mark_price=decimal.Decimal(60))
    assert position_inst.is_short()

    # switching short to long with new mark price
    mark_price = decimal.Decimal(50)
    await position_inst.update(mark_price=mark_price, update_size=decimal.Decimal(0.03))
    assert position_inst.is_long()
    assert position_inst.mark_price == mark_price
    assert position_inst.entry_price == mark_price


async def test_update_update_quantity(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear

    position_inst = personal_data.LinearPosition(trader_inst, default_contract)

    assert position_inst.quantity == constants.ZERO

    quantity = decimal_random_quantity(1)
    await position_inst.update(update_size=quantity)
    assert position_inst.quantity == quantity


async def test__check_and_update_size_with_one_way_position_mode(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear

    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=True)

    if not os.getenv('CYTHON_IGNORE'):
        # LONG
        position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
        await position_inst.update(update_size=decimal.Decimal(10))
        position_inst._check_and_update_size(decimal.Decimal(10))
        assert position_inst.size == decimal.Decimal(20)
        position_inst._check_and_update_size(decimal.Decimal(-10))
        assert position_inst.size == decimal.Decimal(10)
        position_inst._check_and_update_size(decimal.Decimal(-30))
        assert position_inst.size == decimal.Decimal(-20)

        # SHORT
        position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
        await position_inst.update(update_size=decimal.Decimal(-100))
        position_inst._check_and_update_size(decimal.Decimal(-1.5))
        assert position_inst.size == decimal.Decimal(-101.5)
        position_inst._check_and_update_size(decimal.Decimal(51.5))
        assert position_inst.size == decimal.Decimal(-50)
        position_inst._check_and_update_size(decimal.Decimal(100))
        assert position_inst.size == decimal.Decimal(50)


async def test__check_and_update_size_with_hedge_position_mode(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear

    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=False)

    if not os.getenv('CYTHON_IGNORE'):
        # LONG
        position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
        await position_inst.update(update_size=decimal.Decimal(100))
        position_inst._check_and_update_size(decimal.Decimal(-5))
        assert position_inst.size == decimal.Decimal(95)
        position_inst._check_and_update_size(decimal.Decimal("-66.481231232156215215874878"))
        assert position_inst.size == decimal.Decimal("28.518768767843784784125122")
        position_inst._check_and_update_size(decimal.Decimal(-450))
        assert position_inst.size == constants.ZERO  # position should be closed

        # SHORT
        position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
        await position_inst.update(update_size=decimal.Decimal(-10))
        position_inst._check_and_update_size(decimal.Decimal(-10))
        assert position_inst.size == decimal.Decimal(-20)
        position_inst._check_and_update_size(decimal.Decimal(10))
        assert position_inst.size == decimal.Decimal(-10)
        position_inst._check_and_update_size(decimal.Decimal(50))
        assert position_inst.size == constants.ZERO  # position should be closed


async def test__is_update_increasing_size(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear

    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=False)

    if not os.getenv('CYTHON_IGNORE'):
        # Closed
        position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
        assert position_inst._is_update_increasing_size(decimal.Decimal(-5))
        assert position_inst._is_update_increasing_size(decimal.Decimal(5))

        # LONG
        position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
        await position_inst.update(update_size=decimal.Decimal(100))
        assert not position_inst._is_update_increasing_size(decimal.Decimal(-5))
        assert position_inst._is_update_increasing_size(decimal.Decimal(5))

        # SHORT
        position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
        await position_inst.update(update_size=decimal.Decimal(-100))
        assert position_inst._is_update_increasing_size(decimal.Decimal(-5))
        assert not position_inst._is_update_increasing_size(decimal.Decimal(5))


async def test__is_update_closing(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear

    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=False)

    if not os.getenv('CYTHON_IGNORE'):
        # Idle
        position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
        assert position_inst._is_update_closing(decimal.Decimal(-5))
        assert position_inst._is_update_closing(decimal.Decimal(5))

        # LONG
        position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
        await position_inst.update(update_size=decimal.Decimal(100))
        assert not position_inst._is_update_closing(decimal.Decimal(-5))
        assert not position_inst._is_update_closing(decimal.Decimal(5))
        assert not position_inst._is_update_closing(decimal.Decimal(100))
        assert not position_inst._is_update_closing(decimal.Decimal(500))
        assert not position_inst._is_update_closing(decimal.Decimal(99))
        assert position_inst._is_update_closing(decimal.Decimal(-100))
        assert not position_inst._is_update_closing(decimal.Decimal(-99))
        assert position_inst._is_update_closing(decimal.Decimal(-500))

        # SHORT
        position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
        await position_inst.update(update_size=decimal.Decimal(-100))
        assert not position_inst._is_update_closing(decimal.Decimal(-5))
        assert not position_inst._is_update_closing(decimal.Decimal(5))
        assert position_inst._is_update_closing(decimal.Decimal(100))
        assert position_inst._is_update_closing(decimal.Decimal(500))
        assert not position_inst._is_update_closing(decimal.Decimal(99))
        assert not position_inst._is_update_closing(decimal.Decimal(-100))
        assert not position_inst._is_update_closing(decimal.Decimal(-99))
        assert not position_inst._is_update_closing(decimal.Decimal(-500))


async def test_get_quantity_to_close(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear

    position_inst = personal_data.LinearPosition(trader_inst, default_contract)
    quantity = decimal_random_quantity(1)
    await position_inst.update(update_size=quantity)
    assert position_inst.get_quantity_to_close() == -quantity

    position_inst = personal_data.LinearPosition(trader_inst, default_contract)
    quantity = -decimal_random_quantity(1)
    await position_inst.update(update_size=quantity)
    assert position_inst.get_quantity_to_close() == -quantity


async def test_update_size_from_order_with_long_one_way_position(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear

    symbol_contract = default_contract
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=constants.ONE_HUNDRED)

    limit_sell = SellLimitOrder(trader_inst)
    limit_sell.update(order_type=enums.TraderOrderType.SELL_LIMIT,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(10),
                      quantity=decimal.Decimal(2),
                      price=decimal.Decimal(20))
    assert position_inst.update_from_order(limit_sell) == (decimal.Decimal(-2), False)


async def test_update_size_from_order_with_long_close_position_one_way_position(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=constants.ONE_HUNDRED)

    limit_sell = SellLimitOrder(trader_inst)
    limit_sell.update(order_type=enums.TraderOrderType.SELL_LIMIT,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(10),
                      quantity=decimal.Decimal(2),
                      price=decimal.Decimal(20))
    limit_sell.close_position = True
    assert position_inst.update_from_order(limit_sell) == (-constants.ONE_HUNDRED, False)


async def test_update_size_from_order_with_long_reduce_only_one_way_position(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=constants.ONE_HUNDRED)
    position_inst.entry_price = decimal.Decimal(15)

    limit_sell = SellLimitOrder(trader_inst)
    limit_sell.update(order_type=enums.TraderOrderType.SELL_LIMIT,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(10),
                      quantity=constants.ONE_HUNDRED * constants.ONE_HUNDRED,
                      price=decimal.Decimal(20))
    limit_sell.reduce_only = True
    assert position_inst.update_from_order(limit_sell) == (-constants.ONE_HUNDRED, False)

    # reduce only with closed position
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=constants.ZERO)
    limit_sell = SellLimitOrder(trader_inst)
    limit_sell.update(order_type=enums.TraderOrderType.SELL_LIMIT,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(10),
                      quantity=constants.ONE_HUNDRED * constants.ONE_HUNDRED,
                      price=decimal.Decimal(20))
    limit_sell.reduce_only = True
    assert position_inst.update_from_order(limit_sell) == (constants.ZERO, True)


async def test_update_size_from_order_with_long_oversold_one_way_position(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=constants.ONE_HUNDRED)

    limit_sell = SellLimitOrder(trader_inst)
    limit_sell.update(order_type=enums.TraderOrderType.SELL_LIMIT,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(10),
                      quantity=constants.ONE_HUNDRED ** decimal.Decimal(5),
                      price=decimal.Decimal(20))
    assert position_inst.update_from_order(limit_sell) == (-constants.ONE_HUNDRED ** decimal.Decimal(5), False)
    assert position_inst.size == decimal.Decimal("-9999999900")
    assert not position_inst.is_long()


async def test_update_size_from_order_with_short_one_way_position(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=-constants.ONE_HUNDRED)

    buy_limit = BuyLimitOrder(trader_inst)
    buy_limit.update(order_type=enums.TraderOrderType.BUY_LIMIT,
                     symbol=DEFAULT_FUTURE_SYMBOL,
                     current_price=decimal.Decimal(10),
                     quantity=decimal.Decimal(2),
                     price=decimal.Decimal(20))
    assert position_inst.update_from_order(buy_limit) == (decimal.Decimal(2), False)


async def test_update_size_from_order_with_short_close_position_one_way_position(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=-constants.ONE_HUNDRED)

    buy_limit = BuyLimitOrder(trader_inst)
    buy_limit.update(order_type=enums.TraderOrderType.BUY_LIMIT,
                     symbol=DEFAULT_FUTURE_SYMBOL,
                     current_price=decimal.Decimal(10),
                     quantity=decimal.Decimal(2),
                     price=decimal.Decimal(20))
    buy_limit.close_position = True
    assert position_inst.update_from_order(buy_limit) == (constants.ONE_HUNDRED, False)


async def test_update_size_from_order_with_short_reduce_only_one_way_position(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=-constants.ONE_HUNDRED)
    position_inst.entry_price = decimal.Decimal(12)

    buy_limit = BuyLimitOrder(trader_inst)
    buy_limit.update(order_type=enums.TraderOrderType.BUY_LIMIT,
                     symbol=DEFAULT_FUTURE_SYMBOL,
                     current_price=decimal.Decimal(10),
                     quantity=constants.ONE_HUNDRED * constants.ONE_HUNDRED,
                     price=decimal.Decimal(20))
    buy_limit.reduce_only = True
    assert position_inst.update_from_order(buy_limit) == (constants.ONE_HUNDRED, False)

    # reduce only with closed position
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=constants.ZERO)
    buy_limit = BuyLimitOrder(trader_inst)
    buy_limit.update(order_type=enums.TraderOrderType.BUY_LIMIT,
                     symbol=DEFAULT_FUTURE_SYMBOL,
                     current_price=decimal.Decimal(10),
                     quantity=constants.ONE_HUNDRED * constants.ONE_HUNDRED,
                     price=decimal.Decimal(20))
    buy_limit.reduce_only = True
    assert position_inst.update_from_order(buy_limit) == (constants.ZERO, True)


async def test_update_size_from_order_realized_pnl_position(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    symbol_contract.set_position_mode(is_one_way=True)

    mark_price = decimal.Decimal(15)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    position_inst.entry_price = decimal.Decimal(10)
    await position_inst.update(mark_price=mark_price, update_size=-constants.ONE_HUNDRED)

    buy_limit = BuyLimitOrder(trader_inst)
    buy_limit.update(order_type=enums.TraderOrderType.BUY_LIMIT,
                     symbol=DEFAULT_FUTURE_SYMBOL,
                     current_price=mark_price,
                     quantity=constants.ONE,
                     price=decimal.Decimal(21))

    if not os.getenv('CYTHON_IGNORE'):
        with mock.patch.object(buy_limit, "get_total_fees", mock.Mock(return_value=5)):
            assert position_inst.update_from_order(buy_limit) == (constants.ONE, False)
        assert position_inst.size == decimal.Decimal("-99")
        assert position_inst.entry_price == decimal.Decimal("15.15151515151515151515151515")
        assert position_inst.realised_pnl == decimal.Decimal("-5")


async def test_update_size_from_order_with_short_overbought_one_way_position(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=-constants.ONE_HUNDRED)

    buy_limit = BuyLimitOrder(trader_inst)
    buy_limit.update(order_type=enums.TraderOrderType.BUY_LIMIT,
                     symbol=DEFAULT_FUTURE_SYMBOL,
                     current_price=decimal.Decimal(10),
                     quantity=constants.ONE_HUNDRED ** decimal.Decimal(5),
                     price=decimal.Decimal(20))
    assert position_inst.update_from_order(buy_limit) == (constants.ONE_HUNDRED ** decimal.Decimal(5), False)
    assert position_inst.size == decimal.Decimal("9999999900")
    assert not position_inst.is_short()


async def test_update_size_from_order_with_long_oversold_hedge_position(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    symbol_contract.set_position_mode(is_one_way=False)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=constants.ONE_HUNDRED)

    limit_sell = SellLimitOrder(trader_inst)
    limit_sell.update(order_type=enums.TraderOrderType.SELL_LIMIT,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(10),
                      quantity=constants.ONE_HUNDRED ** decimal.Decimal(5),
                      price=decimal.Decimal(20))
    # cannot switch side
    assert position_inst.update_from_order(limit_sell) == (-constants.ONE_HUNDRED, False)
    assert position_inst.size == constants.ZERO
    assert position_inst.is_idle()


async def test_update_size_from_order_with_short_overbought_hedge_position(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    symbol_contract.set_position_mode(is_one_way=False)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=-constants.ONE_HUNDRED)

    buy_limit = BuyLimitOrder(trader_inst)
    buy_limit.update(order_type=enums.TraderOrderType.BUY_LIMIT,
                     symbol=DEFAULT_FUTURE_SYMBOL,
                     current_price=decimal.Decimal(10),
                     quantity=constants.ONE_HUNDRED ** decimal.Decimal(5),
                     price=decimal.Decimal(20))
    # cannot switch side
    assert position_inst.update_from_order(buy_limit) == (constants.ONE_HUNDRED, False)
    assert position_inst.size == constants.ZERO
    assert position_inst.is_idle()


async def test__calculates_size_update_from_filled_order_long_increasing_one_way(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=decimal.Decimal(10))
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(10),
                      quantity=decimal.Decimal(5),
                      price=decimal.Decimal(10))
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_buy, position_inst.get_quantity_to_close()) == decimal.Decimal(5)


async def test__calculates_size_update_from_filled_order_long_increasing_one_way_reduce_only(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=decimal.Decimal(10))
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(10),
                      quantity=decimal.Decimal(5),
                      price=decimal.Decimal(10))
    market_buy.reduce_only = True
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_buy, position_inst.get_quantity_to_close()) == constants.ZERO


async def test__calculates_size_update_from_filled_order_long_decreasing_one_way(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=decimal.Decimal(10))
    market_sell = SellMarketOrder(trader_inst)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=decimal.Decimal(10),
                       quantity=decimal.Decimal(5),
                       price=decimal.Decimal(10))
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_sell, position_inst.get_quantity_to_close()) == -decimal.Decimal(5)


async def test__calculates_size_update_from_filled_order_long_decreasing_reduce_only_one_way(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=decimal.Decimal(10))
    market_sell = SellMarketOrder(trader_inst)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=decimal.Decimal(10),
                       quantity=decimal.Decimal(5),
                       price=decimal.Decimal(10))
    market_sell.reduce_only = True
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_sell, position_inst.get_quantity_to_close()) == -decimal.Decimal(5)


async def test__calculates_size_update_from_filled_order_long_switching_one_way(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=decimal.Decimal(10))
    market_sell = SellMarketOrder(trader_inst)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=decimal.Decimal(10),
                       quantity=decimal.Decimal(20),
                       price=decimal.Decimal(10))
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_sell, position_inst.get_quantity_to_close()) == -decimal.Decimal(20)


async def test__calculates_size_update_from_filled_order_long_switching_reduce_only_one_way(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=decimal.Decimal(10))
    market_sell = SellMarketOrder(trader_inst)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=decimal.Decimal(10),
                       quantity=decimal.Decimal(20),
                       price=decimal.Decimal(10))
    market_sell.reduce_only = True
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_sell, position_inst.get_quantity_to_close()) == -decimal.Decimal(10)


async def test__calculates_size_update_from_filled_order_short_increasing_one_way(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=-decimal.Decimal(10))
    market_sell = SellMarketOrder(trader_inst)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=decimal.Decimal(10),
                       quantity=decimal.Decimal(5),
                       price=decimal.Decimal(10))
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_sell, position_inst.get_quantity_to_close()) == -decimal.Decimal(5)


async def test__calculates_size_update_from_filled_order_short_increasing_one_way_reduce_only(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=-decimal.Decimal(10))
    market_sell = SellMarketOrder(trader_inst)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=decimal.Decimal(10),
                       quantity=decimal.Decimal(5),
                       price=decimal.Decimal(10))
    market_sell.reduce_only = True
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_sell, position_inst.get_quantity_to_close()) == constants.ZERO


async def test__calculates_size_update_from_filled_order_short_decreasing_one_way(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=-decimal.Decimal(10))
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(10),
                      quantity=decimal.Decimal(5),
                      price=decimal.Decimal(10))
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_buy, position_inst.get_quantity_to_close()) == decimal.Decimal(5)


async def test__calculates_size_update_from_filled_order_short_decreasing_reduce_only_one_way(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=-decimal.Decimal(10))
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(10),
                      quantity=decimal.Decimal(5),
                      price=decimal.Decimal(10))
    market_buy.reduce_only = True
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_buy, position_inst.get_quantity_to_close()) == decimal.Decimal(5)


async def test__calculates_size_update_from_filled_order_short_switching_one_way(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=-decimal.Decimal(10))
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(10),
                      quantity=decimal.Decimal(30),
                      price=decimal.Decimal(10))
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_buy, position_inst.get_quantity_to_close()) == decimal.Decimal(30)


async def test__calculates_size_update_from_filled_order_short_switching_reduce_only_one_way(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=-decimal.Decimal(10))
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(10),
                      quantity=decimal.Decimal(30),
                      price=decimal.Decimal(10))
    market_buy.reduce_only = True
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_buy, position_inst.get_quantity_to_close()) == decimal.Decimal(10)


async def test__calculates_size_update_from_filled_order_long_increasing_hedge(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=decimal.Decimal(10))
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(10),
                      quantity=decimal.Decimal(5),
                      price=decimal.Decimal(10))
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_buy, position_inst.get_quantity_to_close()) == decimal.Decimal(5)


async def test__calculates_size_update_from_filled_order_long_increasing_one_way_reduce_only(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=decimal.Decimal(10))
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(10),
                      quantity=decimal.Decimal(5),
                      price=decimal.Decimal(10))
    market_buy.reduce_only = True
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_buy, position_inst.get_quantity_to_close()) == constants.ZERO


async def test__calculates_size_update_from_filled_order_long_decreasing_hedge(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=False)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=decimal.Decimal(10))
    market_sell = SellMarketOrder(trader_inst)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=decimal.Decimal(10),
                       quantity=decimal.Decimal(5),
                       price=decimal.Decimal(10))
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_sell, position_inst.get_quantity_to_close()) == -decimal.Decimal(5)


async def test__calculates_size_update_from_filled_order_long_decreasing_reduce_only_hedge(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=False)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=decimal.Decimal(10))
    market_sell = SellMarketOrder(trader_inst)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=decimal.Decimal(10),
                       quantity=decimal.Decimal(5),
                       price=decimal.Decimal(10))
    market_sell.reduce_only = True
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_sell, position_inst.get_quantity_to_close()) == -decimal.Decimal(5)


async def test__calculates_size_update_from_filled_order_long_switching_hedge(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=False)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=decimal.Decimal(10))
    market_sell = SellMarketOrder(trader_inst)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=decimal.Decimal(10),
                       quantity=decimal.Decimal(20),
                       price=decimal.Decimal(10))
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_sell, position_inst.get_quantity_to_close()) == -decimal.Decimal(10)


async def test__calculates_size_update_from_filled_order_long_switching_reduce_only_hedge(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=False)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=decimal.Decimal(10))
    market_sell = SellMarketOrder(trader_inst)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=decimal.Decimal(10),
                       quantity=decimal.Decimal(20),
                       price=decimal.Decimal(10))
    market_sell.reduce_only = True
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_sell, position_inst.get_quantity_to_close()) == -decimal.Decimal(10)


async def test__calculates_size_update_from_filled_order_short_increasing_hedge(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=False)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=-decimal.Decimal(10))
    market_sell = SellMarketOrder(trader_inst)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=decimal.Decimal(10),
                       quantity=decimal.Decimal(5),
                       price=decimal.Decimal(10))
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_sell, position_inst.get_quantity_to_close()) == -decimal.Decimal(5)


async def test__calculates_size_update_from_filled_order_short_increasing_one_way_reduce_only(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=False)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=-decimal.Decimal(10))
    market_sell = SellMarketOrder(trader_inst)
    market_sell.update(order_type=enums.TraderOrderType.SELL_MARKET,
                       symbol=DEFAULT_FUTURE_SYMBOL,
                       current_price=decimal.Decimal(10),
                       quantity=decimal.Decimal(5),
                       price=decimal.Decimal(10))
    market_sell.reduce_only = True
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_sell, position_inst.get_quantity_to_close()) == constants.ZERO


async def test__calculates_size_update_from_filled_order_short_decreasing_hedge(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=False)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=-decimal.Decimal(10))
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(10),
                      quantity=decimal.Decimal(5),
                      price=decimal.Decimal(10))
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_buy, position_inst.get_quantity_to_close()) == decimal.Decimal(5)


async def test__calculates_size_update_from_filled_order_short_decreasing_reduce_only_hedge(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=False)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=-decimal.Decimal(10))
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(10),
                      quantity=decimal.Decimal(5),
                      price=decimal.Decimal(10))
    market_buy.reduce_only = True
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_buy, position_inst.get_quantity_to_close()) == decimal.Decimal(5)


async def test__calculates_size_update_from_filled_order_short_switching_hedge(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=False)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=-decimal.Decimal(10))
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(10),
                      quantity=decimal.Decimal(30),
                      price=decimal.Decimal(10))
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_buy, position_inst.get_quantity_to_close()) == decimal.Decimal(10)


async def test__calculates_size_update_from_filled_order_short_switching_reduce_only_hedge(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=False)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    await position_inst.update(update_size=-decimal.Decimal(10))
    market_buy = BuyMarketOrder(trader_inst)
    market_buy.update(order_type=enums.TraderOrderType.BUY_MARKET,
                      symbol=DEFAULT_FUTURE_SYMBOL,
                      current_price=decimal.Decimal(10),
                      quantity=decimal.Decimal(30),
                      price=decimal.Decimal(10))
    market_buy.reduce_only = True
    if os.getenv('CYTHON_IGNORE'):
        return
    assert position_inst._calculates_size_update_from_filled_order(
        market_buy, position_inst.get_quantity_to_close()) == decimal.Decimal(10)


async def test_is_order_increasing_size_one_way(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    symbol_contract.set_position_mode(is_one_way=True)
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)

    # orders
    buy_market = BuyMarketOrder(trader_inst)
    reduce_buy_market = BuyMarketOrder(trader_inst)
    reduce_buy_market.reduce_only = True
    close_buy_market = BuyMarketOrder(trader_inst)
    close_buy_market.close_position = True
    sell_market = SellMarketOrder(trader_inst)
    reduce_sell_market = SellMarketOrder(trader_inst)
    reduce_sell_market.reduce_only = True
    close_sell_market = SellMarketOrder(trader_inst)
    close_sell_market.close_position = True

    # when idle
    assert position_inst.is_order_increasing_size(buy_market)
    assert position_inst.is_order_increasing_size(sell_market)
    assert not position_inst.is_order_increasing_size(reduce_buy_market)
    assert not position_inst.is_order_increasing_size(close_buy_market)
    assert not position_inst.is_order_increasing_size(reduce_sell_market)
    assert not position_inst.is_order_increasing_size(close_sell_market)

    # when long
    await position_inst.update(update_size=decimal.Decimal(10))
    assert position_inst.is_order_increasing_size(buy_market)
    assert not position_inst.is_order_increasing_size(sell_market)
    assert not position_inst.is_order_increasing_size(reduce_buy_market)
    assert not position_inst.is_order_increasing_size(close_buy_market)
    assert not position_inst.is_order_increasing_size(reduce_sell_market)
    assert not position_inst.is_order_increasing_size(close_sell_market)

    # when short
    await position_inst.update(update_size=decimal.Decimal(-100))
    assert not position_inst.is_order_increasing_size(buy_market)
    assert position_inst.is_order_increasing_size(sell_market)
    assert not position_inst.is_order_increasing_size(reduce_buy_market)
    assert not position_inst.is_order_increasing_size(close_buy_market)
    assert not position_inst.is_order_increasing_size(reduce_sell_market)
    assert not position_inst.is_order_increasing_size(close_sell_market)


async def test_is_order_increasing_size_hedge(
        future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    symbol_contract = default_contract
    symbol_contract.set_position_mode(is_one_way=False)
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)

    # orders
    buy_market = BuyMarketOrder(trader_inst)
    reduce_buy_market = BuyMarketOrder(trader_inst)
    reduce_buy_market.reduce_only = True
    close_buy_market = BuyMarketOrder(trader_inst)
    close_buy_market.close_position = True
    sell_market = SellMarketOrder(trader_inst)
    reduce_sell_market = SellMarketOrder(trader_inst)
    reduce_sell_market.reduce_only = True
    close_sell_market = SellMarketOrder(trader_inst)
    close_sell_market.close_position = True

    # when idle on long side
    position_inst.side = enums.PositionSide.LONG
    assert position_inst.is_order_increasing_size(buy_market)
    assert not position_inst.is_order_increasing_size(sell_market)
    assert not position_inst.is_order_increasing_size(reduce_buy_market)
    assert not position_inst.is_order_increasing_size(close_buy_market)
    assert not position_inst.is_order_increasing_size(reduce_sell_market)
    assert not position_inst.is_order_increasing_size(close_sell_market)

    # when idle on short side
    position_inst.side = enums.PositionSide.SHORT
    assert not position_inst.is_order_increasing_size(buy_market)
    assert position_inst.is_order_increasing_size(sell_market)
    assert not position_inst.is_order_increasing_size(reduce_buy_market)
    assert not position_inst.is_order_increasing_size(close_buy_market)
    assert not position_inst.is_order_increasing_size(reduce_sell_market)
    assert not position_inst.is_order_increasing_size(close_sell_market)

    # when long
    position_inst.side = enums.PositionSide.LONG
    await position_inst.update(update_size=decimal.Decimal(10))
    assert position_inst.is_order_increasing_size(buy_market)
    assert not position_inst.is_order_increasing_size(sell_market)
    assert not position_inst.is_order_increasing_size(reduce_buy_market)
    assert not position_inst.is_order_increasing_size(close_buy_market)
    assert not position_inst.is_order_increasing_size(reduce_sell_market)
    assert not position_inst.is_order_increasing_size(close_sell_market)

    # when short
    position_inst.side = enums.PositionSide.SHORT
    await position_inst.update(update_size=decimal.Decimal(-100))
    assert not position_inst.is_order_increasing_size(buy_market)
    assert position_inst.is_order_increasing_size(sell_market)
    assert not position_inst.is_order_increasing_size(reduce_buy_market)
    assert not position_inst.is_order_increasing_size(close_buy_market)
    assert not position_inst.is_order_increasing_size(reduce_sell_market)
    assert not position_inst.is_order_increasing_size(close_sell_market)


async def test__update_realized_pnl_from_size_update_long(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear

    tm = exchange_manager_inst.exchange_personal_data.transactions_manager
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    position_inst.update_from_raw({enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL})
    mark_price = constants.ONE
    position_size = decimal.Decimal(10)
    await position_inst.update(mark_price=mark_price, update_size=position_size)

    # update pnl to +50%
    await position_inst.update(mark_price=mark_price * decimal.Decimal(1.5))

    # reduce size by 20% --> 0.2
    await position_inst.update(-position_size * decimal.Decimal(0.2))  # = 0.2
    # = position_size / decimal.Decimal(2) * decimal.Decimal(0.8)
    assert position_inst.unrealised_pnl == decimal.Decimal('3.999999999999999944488848768')
    # = position_size / decimal.Decimal(2) * decimal.Decimal(0.2)
    assert position_inst.realised_pnl == decimal.Decimal('1.000000000000000055511151232')

    assert len(tm.transactions) == 1
    assert list(tm.transactions.values())[-1].symbol == DEFAULT_FUTURE_SYMBOL
    assert list(tm.transactions.values())[-1].realised_pnl == decimal.Decimal('1.000000000000000055511151232')

    position_size = decimal.Decimal(8)

    # reduce size by 50% --> 0.5
    await position_inst.update(-position_size * decimal.Decimal(0.5))
    # = position_size / decimal.Decimal(4) * decimal.Decimal(0.5)
    assert position_inst.unrealised_pnl == decimal.Decimal('1.999999999999999944488848768')
    # = position_size / decimal.Decimal(4) * decimal.Decimal(0.5) + previous realised pnl
    assert position_inst.realised_pnl == decimal.Decimal('3.000000000000000055511151232')

    assert len(tm.transactions) == 2
    assert list(tm.transactions.values())[-1].realised_pnl == decimal.Decimal('3.000000000000000055511151232') - \
           decimal.Decimal('1.000000000000000055511151232')

    position_size = decimal.Decimal(4)

    # Increase by 50% --> shouldn't increase realised pnl
    await position_inst.update(position_size * decimal.Decimal(0.5))
    assert position_inst.realised_pnl == decimal.Decimal('3.000000000000000055511151232')  # = previous realised pnl
    assert len(tm.transactions) == 2


async def test__update_realized_pnl_from_size_update_short(future_trader_simulator_with_default_linear):
    config, exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear

    tm = exchange_manager_inst.exchange_personal_data.transactions_manager
    symbol_contract = default_contract
    exchange_manager_inst.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, symbol_contract)
    symbol_contract.set_position_mode(is_one_way=True)
    position_inst = personal_data.LinearPosition(trader_inst, symbol_contract)
    position_inst.update_from_raw({enums.ExchangeConstantsPositionColumns.SYMBOL.value: DEFAULT_FUTURE_SYMBOL})
    mark_price = constants.ONE
    position_size = decimal.Decimal(100)
    await position_inst.update(mark_price=mark_price, update_size=-position_size)

    # update pnl to +50%
    await position_inst.update(mark_price=mark_price * decimal.Decimal(0.5))

    # reduce size by 30% --> 0.3
    await position_inst.update(position_size * decimal.Decimal(0.3))  # = 0.3
    assert position_inst.unrealised_pnl == decimal.Decimal('35.00000000000000055511151232')
    assert position_inst.realised_pnl == decimal.Decimal('14.99999999999999944488848768')

    assert len(tm.transactions) == 1
    assert list(tm.transactions.values())[-1].symbol == DEFAULT_FUTURE_SYMBOL
    assert list(tm.transactions.values())[-1].realised_pnl == decimal.Decimal('14.99999999999999944488848768')

    position_size = decimal.Decimal(70)

    # reduce size by 40% --> 0.4
    await position_inst.update(position_size * decimal.Decimal(0.4))
    assert position_inst.unrealised_pnl == decimal.Decimal('20.99999999999999977795539508')
    assert position_inst.realised_pnl == decimal.Decimal('29.00000000000000022204460492')

    assert len(tm.transactions) == 2
    assert list(tm.transactions.values())[-1].realised_pnl == decimal.Decimal('29.00000000000000022204460492') - \
           decimal.Decimal('14.99999999999999944488848768')

    position_size = decimal.Decimal(42)

    # Increase by 50% --> shouldn't increase realised pnl
    await position_inst.update(-position_size * decimal.Decimal(0.5))
    assert position_inst.realised_pnl == decimal.Decimal('29.00000000000000022204460492')  # = previous realised pnl
    assert len(tm.transactions) == 2
