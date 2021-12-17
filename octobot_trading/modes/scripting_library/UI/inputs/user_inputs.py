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
import octobot_trading.enums as enums
import octobot_trading.modes as modes


async def user_input(
    ctx,
    name,
    input_type,
    def_val,
    min_val=None,
    max_val=None,
    options=None,
):
    config = ctx.tentacle.trading_config if hasattr(ctx.tentacle, "trading_config") else ctx.tentacle.specific_config
    value = config.get(name.replace(" ", "_"), def_val) if config else def_val
    if not ctx.run_data_writer.are_data_initialized and not await ctx.run_data_writer.contains_row(
            enums.DBTables.INPUTS.value,
            {
                "name": name,
                "tentacle": ctx.tentacle.get_name(),
                "input_type": input_type
            }):
        tentacle_type = "trading_mode" if isinstance(ctx.tentacle, modes.AbstractTradingMode) else "evaluator"
        await ctx.run_data_writer.log(
            enums.DBTables.INPUTS.value,
            {
                "name": name,
                "input_type": input_type,
                "value": value,
                "def_val": def_val,
                "min_val": min_val,
                "max_val": max_val,
                "options": options,
                "tentacle_type": tentacle_type,
                "tentacle": ctx.tentacle.get_name(),
            }
        )
    return value


async def clear_user_inputs(writer):
    await writer.delete(enums.DBTables.INPUTS.value, None)
