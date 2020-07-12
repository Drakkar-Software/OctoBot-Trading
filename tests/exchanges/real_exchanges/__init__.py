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
from contextlib import asynccontextmanager

from octobot_commons.asyncio_tools import wait_asyncio_next_cycle
from octobot_commons.tests.test_config import load_test_config
from octobot_trading.constants import CONFIG_EXCHANGES
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from tests.exchanges import cancel_ccxt_throttle_task


@asynccontextmanager
async def get_exchange_manager(exchange_name, config=None):
    config = config or load_test_config()
    if exchange_name not in config[CONFIG_EXCHANGES]:
        config[CONFIG_EXCHANGES][exchange_name] = {}
    exchange_manager_instance = ExchangeManager(config, exchange_name)
    await exchange_manager_instance.initialize()
    try:
        yield exchange_manager_instance
    finally:
        await exchange_manager_instance.stop()
        cancel_ccxt_throttle_task()
        # let updaters gracefully shutdown
        await wait_asyncio_next_cycle()
