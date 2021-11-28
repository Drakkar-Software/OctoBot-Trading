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
import octobot_commons.errors as commons_errors
import octobot_trading.modes.scripting_library.data as data


def set_script_name(ctx, name):
    ctx.tentacle.script_name = name


async def read_metadata(ctx=None, trading_mode=None, optimizer_id=None):
    trading_mode = trading_mode or ctx.trading_mode_class
    database_manager = databases.DatabaseManager(trading_mode, backtesting_id="1", optimizer_id=optimizer_id)
    try:
        async with data.MetadataReader.database(database_manager.get_backtesting_metadata_identifier()) as reader:
            return await reader.read()
    except commons_errors.DatabaseNotFoundError:
        return []
