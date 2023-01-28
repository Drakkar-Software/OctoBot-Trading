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
from octobot_commons import logging
import octobot_commons.databases as databases
import octobot_tentacles_manager.api as tentacles_manager_api
import octobot_trading.constants as constants
import octobot_commons.constants as common_constants
from octobot_trading.modes.script_keywords import context_management
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

async def get_run_analysis_plots(
    trading_mode, exchange, symbol, analysis_settings, backtesting_id=None, 
    optimizer_id=None, live_id=None, optimization_campaign=None
    ):
    ctx = context_management.Context.minimal(
        trading_mode, logging.get_logger(trading_mode.get_name()), exchange, symbol,
        backtesting_id, optimizer_id, optimization_campaign, 
        analysis_settings, live_id=live_id)
    # TODO: replace with RunAnalysis Mode/Evaluators Factory
    # TODO add scripted RunAnalysis Mode which should be compatible with all trading modes
    if hasattr(trading_mode, "BACKTESTING_SCRIPT_MODULE"):
        return await trading_mode.get_script_from_module(
        trading_mode.BACKTESTING_SCRIPT_MODULE)(ctx)
    import tentacles.RunAnalysis.AnalysisMode.default_run_analysis_mode.run_analysis_mode as run_analysis_mode
    return await run_analysis_mode.DefaultRunAnalysisMode().run_analysis_script(ctx)

def get_run_analysis_settings(
    get_live_settings=True,
    get_backtesting_settings=True,
    ):
    # TODO add API
    return {
        "config": {
            "LiveAnalysisModeSettings": {
                "AnalysisModeSettings": {
                    "ModeName": "DefaulRunAnalysisMode", "EnabledEvaluators": {}
                    },
                "AnalysisModeUserInputs": {}
                }, 
            "BacktestingAnalysisModeSettings": { 
                "AnalysisModeSettings": {
                    "ModeName": "DefaulRunAnalysisMode", "EnabledEvaluators": {}
                    },
                "AnalysisModeUserInputs": {}}, 
            },
        "schema": {
            # json editor schema
            }
        }