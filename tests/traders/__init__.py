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

from octobot_commons.constants import CONFIG_ENABLED_OPTION
from octobot_commons.tests.test_config import load_test_config
from octobot_trading.constants import CONFIG_SIMULATOR, CONFIG_TRADER
from octobot_trading.traders.trader_simulator import TraderSimulator
from octobot_trading.traders.trader import Trader
from tests.exchanges import exchange_manager


@pytest.fixture
async def trader(exchange_manager):
    config = load_test_config()
    config[CONFIG_TRADER][CONFIG_ENABLED_OPTION] = True
    trader_inst = Trader(load_test_config(), exchange_manager)
    await trader_inst.initialize()
    return config, exchange_manager, trader_inst


@pytest.fixture
async def trader_simulator(exchange_manager):
    config = load_test_config()
    config[CONFIG_SIMULATOR][CONFIG_ENABLED_OPTION] = True
    trader_inst = TraderSimulator(load_test_config(), exchange_manager)
    await trader_inst.initialize()
    return config, exchange_manager, trader_inst
