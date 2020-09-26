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
from octobot_backtesting.backtesting import Backtesting

from octobot_commons.tests.test_config import load_test_config
from octobot_trading.exchanges.exchange_manager import ExchangeManager

from octobot_trading.api.exchange import cancel_ccxt_throttle_task

# All test coroutines will be treated as marked.
from octobot_trading.exchanges.types.spot_exchange import SpotExchange
from octobot_trading.exchanges.implementations.spot_exchange_simulator import SpotExchangeSimulator

pytestmark = pytest.mark.asyncio


class TestExchangeManager:
    EXCHANGE_NAME = "binance"

    @staticmethod
    async def init_default(config=None, simulated=True, backtesting=False):
        if not config:
            config = load_test_config()

        exchange_manager = ExchangeManager(config, TestExchangeManager.EXCHANGE_NAME)
        exchange_manager.is_simulated = simulated
        exchange_manager.is_backtesting = backtesting
        if backtesting:
            exchange_manager.backtesting = Backtesting(None, [exchange_manager.id], None, [])
        exchange_manager.rest_only = True

        await exchange_manager.initialize()
        return config, exchange_manager

    async def test_create_exchange(self):
        # simulated
        config, exchange_manager = await self.init_default(simulated=True, backtesting=True)

        assert exchange_manager is not None
        assert exchange_manager.exchange_name is TestExchangeManager.EXCHANGE_NAME

        assert exchange_manager.config is config

        assert isinstance(exchange_manager.exchange, SpotExchangeSimulator)
        await exchange_manager.stop()

        # real
        config, exchange_manager = await self.init_default(simulated=False)

        assert exchange_manager is not None
        assert exchange_manager.exchange_name is TestExchangeManager.EXCHANGE_NAME

        assert exchange_manager.config is config

        assert isinstance(exchange_manager.exchange, SpotExchange)
        cancel_ccxt_throttle_task()
        await exchange_manager.stop()

    async def test_ready(self):
        _, exchange_manager = await self.init_default()

        assert exchange_manager.is_ready
        cancel_ccxt_throttle_task()
        await exchange_manager.stop()
