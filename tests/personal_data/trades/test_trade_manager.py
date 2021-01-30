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

from tests import event_loop
from tests.exchanges import simulated_exchange_manager, simulated_trader

import octobot_trading.personal_data as personal_data

pytestmark = pytest.mark.asyncio


@pytest.fixture
def trade_manager_and_trader(simulated_trader):
    _, _, trader_instance = simulated_trader
    return personal_data.TradesManager(trader_instance), trader_instance


def test_has_closing_trade_with_order_id(trade_manager_and_trader):
    trade_manager, trader = trade_manager_and_trader
    assert trade_manager.has_closing_trade_with_order_id(None) is False
    assert trade_manager.has_closing_trade_with_order_id("None") is False
    trade = personal_data.Trade(trader)
    trade.trade_id = "id"
    trade.is_closing_order = False
    trade.origin_order_id = "None"
    trade_manager.trades["id"] = trade
    # trade is not closing order not has the right origin_order_id
    assert trade_manager.has_closing_trade_with_order_id("id") is False
    # trade does not has the right origin_order_id
    trade.is_closing_order = True
    assert trade_manager.has_closing_trade_with_order_id("id2") is False
    assert trade_manager.has_closing_trade_with_order_id("id") is False
    trade.origin_order_id = "id"
    # trade is closing this order
    assert trade_manager.has_closing_trade_with_order_id("id") is True
