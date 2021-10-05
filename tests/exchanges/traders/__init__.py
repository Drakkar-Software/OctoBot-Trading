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

import octobot_commons.constants as commons_constants
from octobot_commons.tests.test_config import load_test_config
import octobot_trading.constants as constants
import octobot_trading.enums as enums
import octobot_trading.exchange_data.contracts as contracts
from octobot_trading.exchanges.traders.trader_simulator import TraderSimulator
from octobot_trading.exchanges.traders.trader import Trader


async def create_trader_from_exchange_manager(exchange_manager, simulated=False):
    config = load_test_config()
    if simulated:
        config[commons_constants.CONFIG_SIMULATOR][commons_constants.CONFIG_ENABLED_OPTION] = True
        trader_inst = TraderSimulator(load_test_config(), exchange_manager)
    else:
        config[commons_constants.CONFIG_TRADER][commons_constants.CONFIG_ENABLED_OPTION] = True
        trader_inst = Trader(load_test_config(), exchange_manager)
    await trader_inst.initialize()
    return config, exchange_manager, trader_inst


@pytest.fixture
async def trader(exchange_manager):
    return await create_trader_from_exchange_manager(exchange_manager)


@pytest.fixture
async def margin_trader(margin_exchange_manager):
    return await create_trader_from_exchange_manager(margin_exchange_manager)


@pytest.fixture
async def future_trader(future_exchange_manager):
    return await create_trader_from_exchange_manager(future_exchange_manager)


@pytest.fixture
async def trader_simulator(simulated_exchange_manager):
    return await create_trader_from_exchange_manager(simulated_exchange_manager, simulated=True)


@pytest.fixture
async def margin_trader_simulator(margin_simulated_exchange_manager):
    return await create_trader_from_exchange_manager(margin_simulated_exchange_manager, simulated=True)

DEFAULT_FUTURE_SYMBOL = "BTC/USDT"

@pytest.fixture
async def future_trader_simulator(future_simulated_exchange_manager):
    default_future_symbol_contract = contracts.FutureContract(DEFAULT_FUTURE_SYMBOL)
    default_future_symbol_contract.current_leverage = constants.ONE
    default_future_symbol_contract.margin_type = enums.MarginType.ISOLATED
    default_future_symbol_contract.contract_type = enums.FutureContractType.PERPETUAL
    future_simulated_exchange_manager.exchange.set_pair_future_contract(DEFAULT_FUTURE_SYMBOL,
                                                                        default_future_symbol_contract)
    return await create_trader_from_exchange_manager(future_simulated_exchange_manager, simulated=True)
