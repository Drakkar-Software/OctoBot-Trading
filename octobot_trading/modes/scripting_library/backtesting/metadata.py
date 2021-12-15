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
import copy


import octobot_commons.databases as databases
import octobot_commons.errors as commons_errors
import octobot_trading.modes.scripting_library.data as data
import octobot_trading.enums as enums


def set_script_name(ctx, name):
    ctx.tentacle.script_name = name


async def _get_optimizer_metadata_wrapper(db_manager, metadata_list):
    sample_run = metadata_list[0]
    default_pnl = sample_run.get(enums.BacktestingMetadata.PNL_PERCENT.value, 0)
    for metadata in metadata_list:
        if metadata.get(enums.BacktestingMetadata.PNL_PERCENT.value, default_pnl) > \
           sample_run.get(enums.BacktestingMetadata.PNL_PERCENT.value, default_pnl):
            sample_run = metadata
        metadata[enums.BacktestingMetadata.OPTIMIZER_ID.value] = db_manager.optimizer_id
    sample_run = copy.deepcopy(sample_run)
    sample_run[enums.BacktestingMetadata.CHILDREN.value] = metadata_list
    return sample_run


async def _read_backtesting_metadata(db_manager, metadata_list):
    async with data.MetadataReader.database(db_manager.get_backtesting_metadata_identifier()) \
            as reader:
        try:
            metadata_list += await reader.read()
        except commons_errors.DatabaseNotFoundError:
            pass


async def read_metadata(ctx=None, trading_mode=None, include_optimizer_runs=False):
    trading_mode = trading_mode or ctx.trading_mode.__class__
    metadata = []
    optimizer_data_managers = []
    backtesting_database_manager = databases.DatabaseManager(trading_mode, backtesting_id="1")
    if include_optimizer_runs:
        optimizer_ids = await backtesting_database_manager.get_optimizer_run_ids()
        optimizer_data_managers = [databases.DatabaseManager(trading_mode, optimizer_id=optimizer_id)
                                   for optimizer_id in optimizer_ids]
    await _read_backtesting_metadata(backtesting_database_manager, metadata)
    for database_manager in optimizer_data_managers:
        optimizer_metadata = []
        await _read_backtesting_metadata(database_manager, optimizer_metadata)
        if optimizer_metadata:
            metadata.append(await _get_optimizer_metadata_wrapper(database_manager, optimizer_metadata))
    return metadata
