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
import octobot_trading.enums as enums
import octobot_trading.modes as modes
import octobot_trading.modes.scripting_library.TA.trigger.eval_triggered as eval_triggered
import octobot_tentacles_manager.api as tentacles_manager_api


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
    show_in_optimizer=True
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
        show_in_optimizer=show_in_optimizer
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
    show_in_optimizer=True
):
    if is_nested_config is None:
        is_nested_config = ctx.is_nested_tentacle
    if not ctx.run_data_writer.are_data_initialized and not await ctx.run_data_writer.contains_row(
            enums.DBTables.INPUTS.value,
            {
                "name": name,
                "tentacle": ctx.tentacle.get_name(),
                "nested_tentacle": nested_tentacle,
                "input_type": input_type,
                "is_nested_config": is_nested_config
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
                "nested_tentacle": nested_tentacle,
                "is_nested_config": is_nested_config,
                "in_summary": show_in_summary,
                "in_optimizer": show_in_optimizer,
            }
        )


def _find_configuration(nested_configuration, nested_config_names, element):
    for key, config in nested_configuration.items():
        if len(nested_config_names) == 0 and key == element:
            return config
        if isinstance(config, dict) and (len(nested_config_names) == 0 or key == nested_config_names[0]):
            found_config = _find_configuration(config, nested_config_names[1:], element)
            if found_config is not None:
                return found_config
    return None


async def external_user_input(
    ctx,
    name,
    tentacle,
    config_name=None,
    trigger_if_necessary=True,
    config: dict = None
):
    if config_name is None:
        query = await ctx.run_data_writer.search()
        raw_value = await ctx.run_data_writer.select(
            enums.DBTables.INPUTS.value,
            (query.name == name) & (query.tentacle == tentacle)
        )
        if raw_value:
            return raw_value[0]["value"]
    else:
        # look for the user input in non nested user inputs
        user_inputs = await get_user_inputs(ctx.run_data_writer)
        # First try with the current top level tentacle (faster and to avoid name conflicts), then use all tentacles
        top_tentacle_config = ctx.top_level_tentacle.specific_config \
            if hasattr(ctx.top_level_tentacle, "specific_config") else ctx.top_level_tentacle.trading_config
        tentacle_config = _find_configuration(top_tentacle_config,
                                              ctx.nested_config_names,
                                              config_name.replace(" ", "_"))
        if tentacle_config is None:
            for local_user_input in user_inputs:
                if not local_user_input["is_nested_config"] and \
                   local_user_input["input_type"] == commons_constants.NESTED_TENTACLE_CONFIG:
                    tentacle_config = _find_configuration(local_user_input["value"],
                                                          ctx.nested_config_names,
                                                          config_name.replace(" ", "_"))
                    if tentacle_config is not None:
                        break
        if tentacle_config is None and trigger_if_necessary:
            tentacle_class = tentacles_manager_api.get_tentacle_class_from_string(tentacle) \
                if isinstance(tentacle, str) else tentacle
            _, tentacle_config = await eval_triggered._trigger_single_evaluation(
                ctx, tentacle_class,
                commons_enums.CacheDatabaseColumns.VALUE.value,
                config_name, config)
        try:
            return None if tentacle_config is None else tentacle_config[name.replace(" ", "_")]
        except KeyError:
            return None
    return None


async def get_user_inputs(reader):
    return await reader.all(enums.DBTables.INPUTS.value)


async def clear_user_inputs(writer):
    await writer.delete(enums.DBTables.INPUTS.value, None)
