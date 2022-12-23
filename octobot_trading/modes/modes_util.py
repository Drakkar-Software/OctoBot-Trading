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
import octobot_commons.databases as databases
import octobot_tentacles_manager.api as tentacles_manager_api
import octobot_trading.constants as constants
import octobot_commons.constants as common_constants
import octobot_trading.modes.script_keywords.basic_keywords as basic_keywords


def get_required_candles_count(trading_mode_class, tentacles_setup_config):
    return tentacles_manager_api.get_tentacle_config(tentacles_setup_config, trading_mode_class).get(
        constants.CONFIG_CANDLES_HISTORY_SIZE_KEY,
        common_constants.DEFAULT_IGNORED_VALUE
    )


async def clear_simulated_orders_cache(trading_mode):
    await basic_keywords.clear_orders_cache(
        databases.RunDatabasesProvider.instance().get_orders_db(
            trading_mode.bot_id, trading_mode.exchange_manager.exchange_name
        )
    )


async def clear_plotting_cache(trading_mode):
    await basic_keywords.clear_symbol_plot_cache(
        databases.RunDatabasesProvider.instance().get_symbol_db(
            trading_mode.bot_id, trading_mode.exchange_manager.exchange_name, trading_mode.symbol
        )
    )
