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
import decimal

import octobot_trading.modes.scripting_library.UI.inputs.user_inputs as user_inputs


async def user_select_leverage(
        ctx,
        def_val=1,
        name="leverage"):
    selected_leverage = await user_inputs.user_input(ctx, name, "int", def_val)
    if ctx.exchange_manager.is_future:
        side = None
        # TODO remove this try when bybit tentacle is up
        try:
            await ctx.exchange_manager.trader.set_leverage(ctx.symbol, side, decimal.Decimal(str(selected_leverage)))
        except AttributeError:
            ctx.logger.warning("TODO: rebase tentacles when bybit exchange is up")
    return selected_leverage
