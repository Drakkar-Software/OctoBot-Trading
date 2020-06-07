#  Drakkar-Software OctoBot
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
from octobot_trading.enums import TradeOrderSide, OrderStatus, TraderOrderType
from octobot_trading.data.order import Order
from tests.exchanges import exchange_manager
from tests.traders import trader_simulator
from tests.traders import trader
from tests.util.random_numbers import random_price

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_get_profitability(trader_simulator):
    config, exchange_manager_inst, trader_inst = trader_simulator

    # Test filled_price > create_last_price
    # test side SELL
    order_filled_sup_side_sell_inst = Order(trader_inst)
    order_filled_sup_side_sell_inst.side = TradeOrderSide.SELL
    order_filled_sup_side_sell_inst.filled_price = 10
    order_filled_sup_side_sell_inst.created_last_price = 9
    assert order_filled_sup_side_sell_inst.get_profitability() == (-(1 - 10 / 9))

    # test side BUY
    order_filled_sup_side_sell_inst = Order(trader_inst)
    order_filled_sup_side_sell_inst.side = TradeOrderSide.BUY
    order_filled_sup_side_sell_inst.filled_price = 15.114778
    order_filled_sup_side_sell_inst.created_last_price = 7.265
    assert order_filled_sup_side_sell_inst.get_profitability() == (1 - 15.114778 / 7.265)

    # Test filled_price < create_last_price
    # test side SELL
    order_filled_sup_side_sell_inst = Order(trader_inst)
    order_filled_sup_side_sell_inst.side = TradeOrderSide.SELL
    order_filled_sup_side_sell_inst.filled_price = 11.556877
    order_filled_sup_side_sell_inst.created_last_price = 20
    assert order_filled_sup_side_sell_inst.get_profitability() == (1 - 20 / 11.556877)

    # test side BUY
    order_filled_sup_side_sell_inst = Order(trader_inst)
    order_filled_sup_side_sell_inst.side = TradeOrderSide.BUY
    order_filled_sup_side_sell_inst.filled_price = 8
    order_filled_sup_side_sell_inst.created_last_price = 14.35
    assert order_filled_sup_side_sell_inst.get_profitability() == (-(1 - 14.35 / 8))

    # Test filled_price == create_last_price
    # test side SELL
    order_filled_sup_side_sell_inst = Order(trader_inst)
    order_filled_sup_side_sell_inst.side = TradeOrderSide.SELL
    order_filled_sup_side_sell_inst.filled_price = 1517374.4567
    order_filled_sup_side_sell_inst.created_last_price = 1517374.4567
    assert order_filled_sup_side_sell_inst.get_profitability() == 0

    # test side BUY
    order_filled_sup_side_sell_inst = Order(trader_inst)
    order_filled_sup_side_sell_inst.side = TradeOrderSide.BUY
    order_filled_sup_side_sell_inst.filled_price = 0.4275587387858527
    order_filled_sup_side_sell_inst.created_last_price = 0.4275587387858527
    assert order_filled_sup_side_sell_inst.get_profitability() == 0


async def test_update(trader):
    config, exchange_manager_inst, trader_inst = trader

    # with real trader
    order_inst = Order(trader_inst)
    order_inst.update(order_type=TraderOrderType.BUY_MARKET,
                      symbol="BTC/USDT",
                      current_price=10000,
                      quantity=1)

    assert order_inst.order_type == TraderOrderType.BUY_MARKET
    assert order_inst.symbol == "BTC/USDT"
    assert order_inst.created_last_price == 10000
    assert order_inst.origin_quantity == 1
    assert order_inst.creation_time != 0
    assert order_inst.get_currency_and_market() == ('BTC', 'USDT')
    assert order_inst.side is None
    assert order_inst.status == OrderStatus.OPEN
    assert order_inst.filled_quantity != order_inst.origin_quantity

    order_inst.update(order_type=TraderOrderType.STOP_LOSS_LIMIT,
                      symbol="ETH/BTC",
                      quantity=0.1,
                      quantity_filled=5.2,
                      price=0.12,
                      stop_price=0.9)
    assert order_inst.origin_stop_price == 0.9
    assert order_inst.origin_price == 0.12


async def test_simulated_update(trader_simulator):
    config, exchange_manager_inst, trader_inst = trader_simulator
    order_sim_inst = Order(trader_inst)

    order_sim_inst.update(order_type=TraderOrderType.SELL_MARKET,
                          symbol="LTC/USDT",
                          quantity=100,
                          price=3.22)
    assert order_sim_inst.status == OrderStatus.OPEN
    assert order_sim_inst.filled_quantity == order_sim_inst.origin_quantity == 100
