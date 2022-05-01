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

import octobot_commons.enums as commons_enums
import octobot_commons.constants as commons_constants


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
    order=None,
    flush_if_necessary=False
):
    """
    Set and return a user input value.
    Types are: int, float, boolean, options, multiple-options, text
    :return:
    """
    tentacle_type_str = "trading_mode" if hasattr(ctx.tentacle, "trading_config") else "evaluator"
    config = ctx.tentacle.trading_config if tentacle_type_str == "trading_mode" else ctx.tentacle.specific_config
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
        tentacle_type_str,
        min_val=min_val,
        max_val=max_val,
        options=options,
        is_nested_config=is_nested_config,
        nested_tentacle=nested_tentacle,
        show_in_summary=show_in_summary,
        show_in_optimizer=show_in_optimizer,
        order=order,
        flush_if_necessary=flush_if_necessary
    )
    return value


async def save_user_input(
    ctx,
    name,
    input_type,
    value,
    def_val,
    tentacle_type_str,
    min_val=None,
    max_val=None,
    options=None,
    is_nested_config=None,
    nested_tentacle=None,
    show_in_summary=True,
    show_in_optimizer=True,
    order=None,
    flush_if_necessary=False
):
    if is_nested_config is None:
        is_nested_config = ctx.is_nested_tentacle
    if not await ctx.run_data_writer.contains_row(
            commons_enums.DBTables.INPUTS.value,
            {
                "name": name,
                "tentacle": ctx.tentacle.get_name(),
                "nested_tentacle": nested_tentacle,
                "is_nested_config": is_nested_config
            }):
        await ctx.run_data_writer.log(
            commons_enums.DBTables.INPUTS.value,
            {
                "name": name,
                "input_type": input_type,
                "value": value,
                "def_val": def_val,
                "min_val": min_val,
                "max_val": max_val,
                "options": options,
                "tentacle_type": tentacle_type_str,
                "tentacle": ctx.tentacle.get_name(),
                "nested_tentacle": nested_tentacle,
                "is_nested_config": is_nested_config,
                "in_summary": show_in_summary,
                "in_optimizer": show_in_optimizer,
                "order": order
            }
        )
        if not ctx.exchange_manager.is_backtesting and (flush_if_necessary or ctx.run_data_writer.are_data_initialized):
            # in some cases, user inputs might be setup after the 1st trading mode cycle: flush
            # writer in live mode to ensure writing
            await ctx.run_data_writer.flush()


async def get_user_inputs(reader):
    return await reader.all(commons_enums.DBTables.INPUTS.value)


async def clear_user_inputs(writer):
    await writer.delete(commons_enums.DBTables.INPUTS.value, None)


async def get_activation_topics(context, default_value, options):
    return await user_input(
        context, commons_constants.CONFIG_ACTIVATION_TOPICS, "options",
        default_value,
        options=options,
        show_in_optimizer=False, show_in_summary=False, order=1000
    )
