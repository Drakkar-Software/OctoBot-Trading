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
import os

import pytest

import octobot_trading.enums as enums
import octobot_trading.personal_data.positions.positions_manager as positions_mgr
from tests import event_loop
from tests.exchanges import future_simulated_exchange_manager
from tests.exchanges.traders import future_trader_simulator, DEFAULT_FUTURE_SYMBOL_CONTRACT, DEFAULT_FUTURE_SYMBOL
from tests import event_loop

# All test coroutines will be treated as marked.
from tests.personal_data import DEFAULT_MARKET_QUANTITY
from tests.test_utils.random_numbers import decimal_random_price, decimal_random_quantity

pytestmark = pytest.mark.asyncio


async def test__generate_position_id(future_trader_simulator):
    config, exchange_manager, trader = future_trader_simulator
    positions_manager = exchange_manager.exchange_personal_data.positions_manager
    symbol_contract = DEFAULT_FUTURE_SYMBOL_CONTRACT
    trader.exchange_manager.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL, DEFAULT_FUTURE_SYMBOL_CONTRACT)

    if not os.getenv('CYTHON_IGNORE'):
        symbol_contract.set_position_mode(is_one_way=True)
        assert positions_manager._generate_position_id(DEFAULT_FUTURE_SYMBOL, None) == \
               DEFAULT_FUTURE_SYMBOL
        symbol_contract.set_position_mode(is_one_way=False)
        assert positions_manager._generate_position_id(DEFAULT_FUTURE_SYMBOL, enums.PositionSide.LONG) == \
               DEFAULT_FUTURE_SYMBOL + positions_mgr.PositionsManager.POSITION_ID_SEPARATOR \
               + enums.PositionSide.LONG.value
        assert positions_manager._generate_position_id(DEFAULT_FUTURE_SYMBOL, enums.PositionSide.SHORT) == \
               DEFAULT_FUTURE_SYMBOL + positions_mgr.PositionsManager.POSITION_ID_SEPARATOR \
               + enums.PositionSide.SHORT.value
