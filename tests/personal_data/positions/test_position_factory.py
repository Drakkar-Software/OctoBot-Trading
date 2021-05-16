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
import octobot_trading.errors as errors
import octobot_trading.enums as enums
import octobot_trading.personal_data as personal_data

from tests import event_loop
from tests.exchanges import exchange_manager
from tests.exchanges.traders import trader_simulator
from tests.exchanges.traders import trader
from tests.test_utils.random_numbers import random_price

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_create_position_instance_from_raw(trader_simulator):
    config, exchange_manager_inst, trader_inst = trader_simulator

    raw_position = {
        enums.ExchangeConstantsPositionColumns.SYMBOL.value: "BTC/USDT",
        enums.ExchangeConstantsPositionColumns.STATUS.value: enums.PositionStatus.ADL.value
    }
    position = personal_data.create_position_instance_from_raw(trader_inst, raw_position)
    position_open = personal_data.create_position_instance_from_raw(trader_inst, raw_position, force_open=True)
    assert position.symbol == "BTC/USDT"
    assert position.market == "USDT"
    assert position.currency == "BTC"
    assert position.status == enums.PositionStatus.ADL
    assert position_open.status == enums.PositionStatus.OPEN
