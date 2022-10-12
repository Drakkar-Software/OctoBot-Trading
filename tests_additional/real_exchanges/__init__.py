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
import contextlib

import octobot_commons.constants as commons_constants
import octobot_commons.asyncio_tools as asyncio_tools
import octobot_commons.tests.test_config as test_config
import octobot_trading.api as api
import octobot_trading.exchanges as exchanges
import octobot_trading.enums as enums
import octobot_trading.errors as errors


@contextlib.asynccontextmanager
async def get_exchange_manager(exchange_name, config=None):
    config = {**test_config.load_test_config(), **config} if config else test_config.load_test_config()
    if exchange_name not in config[commons_constants.CONFIG_EXCHANGES]:
        config[commons_constants.CONFIG_EXCHANGES][exchange_name] = {}
    exchange_manager_instance = exchanges.ExchangeManager(config, exchange_name)
    if config[commons_constants.CONFIG_EXCHANGES][exchange_name]. \
       get(commons_constants.CONFIG_EXCHANGE_TYPE, enums.ExchangeTypes.SPOT.value) == enums.ExchangeTypes.FUTURE.value:
        exchange_manager_instance.is_future = True
    await exchange_manager_instance.initialize()
    try:
        yield exchange_manager_instance
    except errors.UnreachableExchange as err:
        raise errors.UnreachableExchange(f"{exchange_name} can't be reached, it is either offline or you are not connected "
                                         "to the internet (or a proxy is preventing connecting to this exchange).") \
            from err
    finally:
        await exchange_manager_instance.stop()
        api.cancel_ccxt_throttle_task()
        # let updaters gracefully shutdown
        await asyncio_tools.wait_asyncio_next_cycle()
