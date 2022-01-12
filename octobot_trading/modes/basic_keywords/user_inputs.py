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

import octobot_trading.enums as trading_enums
import octobot_trading.modes.abstract_trading_mode as abstract_trading_mode


async def user_input(
    ctx,
    name,
    input_type,
    def_val,
    min_val=None,
    max_val=None,
    options=None,
    is_nested_config=None,
    nested_tentacle=None,
    show_in_summary=True,
    show_in_optimizer=True,
    flush_if_necessary=False
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
        is_nested_config=is_nested_config,
        nested_tentacle=nested_tentacle,
        show_in_summary=show_in_summary,
        show_in_optimizer=show_in_optimizer,
        flush_if_necessary=flush_if_necessary
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
    is_nested_config=None,
    nested_tentacle=None,
    show_in_summary=True,
    show_in_optimizer=True,
    flush_if_necessary=False
):
    if is_nested_config is None:
        is_nested_config = ctx.is_nested_tentacle
    if not await ctx.run_data_writer.contains_row(
            trading_enums.DBTables.INPUTS.value,
            {
                "name": name,
                "tentacle": ctx.tentacle.get_name(),
                "nested_tentacle": nested_tentacle,
                "input_type": input_type,
                "is_nested_config": is_nested_config
            }):
        tentacle_type = "trading_mode" if isinstance(ctx.tentacle, abstract_trading_mode.AbstractTradingMode) \
            else "evaluator"
        await ctx.run_data_writer.log(
            trading_enums.DBTables.INPUTS.value,
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
                "nested_tentacle": nested_tentacle,
                "is_nested_config": is_nested_config,
                "in_summary": show_in_summary,
                "in_optimizer": show_in_optimizer,
            }
        )
        if (flush_if_necessary or ctx.run_data_writer.are_data_initialized) and not ctx.exchange_manager.is_backtesting:
            # in some cases, user inputs might be setup after the 1st trading mode cycle: flush
            # writer in live mode to ensure writing
            await ctx.run_data_writer.flush()


async def get_user_inputs(reader):
    return await reader.all(trading_enums.DBTables.INPUTS.value)


async def clear_user_inputs(writer):
    await writer.delete(trading_enums.DBTables.INPUTS.value, None)
