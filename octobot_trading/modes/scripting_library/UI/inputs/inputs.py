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


async def user_input(
    ctx,
    name,
    input_type,
    def_val,
    min_val=None,
    max_val=None,
    options=None,
):
    value = ctx.current_trading_mode_producer.trading_mode.trading_config.get(name.replace(" ", "_"), None) \
        if ctx.current_trading_mode_producer.trading_mode.trading_config else None
    input_query = await ctx.writer.search()
    if not ctx.writer.are_data_initialized and await ctx.writer.count(
            enums.DBTables.INPUTS.value,
            (input_query.name == name)
            & (input_query.input_type == input_type)) == 0:
        await ctx.writer.log(
            enums.DBTables.INPUTS.value,
            {
                "name": name,
                "input_type": input_type,
                "value": value,
                "def_val": def_val,
                "min_val": min_val,
                "max_val": max_val,
                "options": options,
                "tentacle": ctx.trading_mode_class.get_name(),
            }
        )
    return value
