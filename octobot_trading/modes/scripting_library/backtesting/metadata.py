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
import octobot_trading.modes.scripting_library.data as data


def set_script_name(ctx, name):
    ctx.tentacle.script_name = name


def get_backtesting_db(ctx, run_id, optimizer_id=None):
    return ctx.trading_mode_class.get_db_name(
        prefix=run_id,
        backtesting=True,
        optimizer_id=optimizer_id,
    )


async def read_metadata(ctx=None, trading_mode=None, backtesting=True, optimizer_id=None):
    trading_mode = trading_mode or ctx.trading_mode_class
    data_file = trading_mode.get_db_name(metadata_db=True, backtesting=backtesting, optimizer_id=optimizer_id)
    async with data.MetadataReader.database(data_file) as reader:
        return await reader.read()
