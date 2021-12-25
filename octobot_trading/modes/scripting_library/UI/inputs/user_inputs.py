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
    config_name=None,
    not_important=False  # todo when true hide from optimizer inputs and all tables
):
    config = ctx.tentacle.trading_config if hasattr(ctx.tentacle, "trading_config") else ctx.tentacle.specific_config
    try:
        value = config[name.replace(" ", "_")]
    except KeyError:
        config[name.replace(" ", "_")] = def_val
        value = def_val
    await save_user_input(
        ctx,
        name,
        input_type,
        value,
        def_val,
        min_val=min_val,
        max_val=max_val,
        options=options,
        config_name=config_name,
        not_important=not_important
    )
    return value


async def save_user_input(
        ctx,
        name,
        input_type,
        value,
        def_val,
        min_val=None,
        max_val=None,
        options=None,
        config_name=None,
        not_important=False
):
    config_name = config_name or ctx.nested_config_name
    if not ctx.run_data_writer.are_data_initialized and not await ctx.run_data_writer.contains_row(
            enums.DBTables.INPUTS.value,
            {
                "name": name,
                "tentacle": ctx.tentacle.get_name(),
                "input_type": input_type,
                "config_name": config_name
            }):
        tentacle_type = "trading_mode" if isinstance(ctx.tentacle, modes.AbstractTradingMode) else "evaluator"
        await ctx.run_data_writer.log(
            enums.DBTables.INPUTS.value,
            {
                "name": name,
                "input_type": input_type,
                "config_name": config_name,
                "value": value,
                "def_val": def_val,
                "min_val": min_val,
                "max_val": max_val,
                "options": options,
                "tentacle_type": tentacle_type,
                "tentacle": ctx.tentacle.get_name(),
            }
        )


async def external_user_input(
    ctx,
    name,
    tentacle
):
    query = await ctx.run_data_writer.search()
    raw_value = await ctx.run_data_writer.select(
        enums.DBTables.INPUTS.value,
        (query.name == name) & (query.tentacle == tentacle)
    )
    if raw_value:
        return raw_value[0]["value"]
    return None


async def get_user_inputs(reader):
    return await reader.all(enums.DBTables.INPUTS.value)


async def clear_user_inputs(writer):
    await writer.delete(enums.DBTables.INPUTS.value, None)
