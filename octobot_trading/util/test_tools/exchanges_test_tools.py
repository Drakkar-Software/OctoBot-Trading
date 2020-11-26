#  Drakkar-Software OctoBot-Private-Tentacles
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

import octobot_commons.asyncio_tools as asyncio_tools
import octobot_trading.api as trading_api
import octobot_trading.exchanges as exchanges


async def create_test_exchange_manager(
        config: object,
        exchange_name: str,
        is_spot_only: bool = True,
        is_margin: bool = False,
        is_future: bool = False) -> exchanges.ExchangeManager:
    exchange_manager_instance = exchanges.ExchangeManager(config, exchange_name)
    exchange_manager_instance.is_spot_only = is_spot_only
    exchange_manager_instance.is_margin = is_margin
    exchange_manager_instance.is_future = is_future
    await exchange_manager_instance.initialize()
    return exchange_manager_instance


async def stop_test_exchange_manager(exchange_manager_instance: exchanges.ExchangeManager):
    trading_api.cancel_ccxt_throttle_task()
    await exchange_manager_instance.stop()
    # let updaters gracefully shutdown
    await asyncio_tools.wait_asyncio_next_cycle()
