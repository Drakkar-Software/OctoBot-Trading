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
import octobot_commons.constants as commons_constants
import octobot_trading.api as trading_api
import octobot_trading.exchanges as exchanges
import octobot_tentacles_manager.api as tentacles_manager_api


async def create_test_exchange_manager(
        config: object,
        exchange_name: str,
        is_spot_only: bool = True,
        is_margin: bool = False,
        is_future: bool = False,
        rest_only: bool = False,
        is_real: bool = True,
        is_sandboxed: bool = False,
        ignore_exchange_config: bool = True) -> exchanges.ExchangeManager:
    if ignore_exchange_config:
        # enable exchange name in config
        config[commons_constants.CONFIG_EXCHANGES][exchange_name] = {commons_constants.CONFIG_ENABLED_OPTION: True}

    builder = exchanges.create_exchange_builder_instance(config, exchange_name)
    builder.disable_trading_mode()
    builder.use_tentacles_setup_config(tentacles_manager_api.get_tentacles_setup_config())
    if is_spot_only:
        builder.is_spot_only()
    if is_margin:
        builder.is_margin()
    if is_future:
        builder.is_future()
    if rest_only:
        builder.is_rest_only()
    if is_sandboxed:
        builder.is_sandboxed(is_sandboxed)
    if is_real:
        builder.is_real()
    else:
        builder.is_simulated()
    await builder.build()
    return builder.exchange_manager


async def stop_test_exchange_manager(exchange_manager_instance: exchanges.ExchangeManager):
    trading_api.cancel_ccxt_throttle_task()
    await exchange_manager_instance.stop()
    # let updaters gracefully shutdown
    await asyncio_tools.wait_asyncio_next_cycle()
