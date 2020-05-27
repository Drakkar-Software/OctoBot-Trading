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

from octobot_trading.orders.types import BuyLimitOrder, SellLimitOrder, SellMarketOrder, BuyMarketOrder, StopLossOrder, \
    StopLossLimitOrder

from tests import event_loop
from tests.exchanges import simulated_trader, simulated_exchange_manager


@pytest.fixture()
def buy_limit_order(event_loop, simulated_trader):
    _, _, trader_instance = simulated_trader
    return BuyLimitOrder(trader_instance)


@pytest.fixture()
def sell_limit_order(event_loop, simulated_trader):
    _, _, trader_instance = simulated_trader
    return SellLimitOrder(trader_instance)


@pytest.fixture()
def buy_market_order(event_loop, simulated_trader):
    _, _, trader_instance = simulated_trader
    return BuyMarketOrder(trader_instance)


@pytest.fixture()
def sell_market_order(event_loop, simulated_trader):
    _, _, trader_instance = simulated_trader
    return SellMarketOrder(trader_instance)


@pytest.fixture()
def stop_loss_order(event_loop, simulated_trader):
    _, _, trader_instance = simulated_trader
    return StopLossOrder(trader_instance)


@pytest.fixture()
def stop_loss_limit_order(event_loop, simulated_trader):
    _, _, trader_instance = simulated_trader
    return StopLossLimitOrder(trader_instance)
