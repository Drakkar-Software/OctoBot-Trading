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

import octobot_commons.time_frame_manager as time_frame_manager
from .user_inputs import user_input


async def user_select_time_frame(
        ctx,
        def_val="1h",
        name="Timeframe",

):
    available_timeframes = time_frame_manager.sort_time_frames(ctx.exchange_manager.client_time_frames)
    selected_timeframe = await user_input(ctx, name, "options", def_val, options=available_timeframes)
    return selected_timeframe


async def user_multi_select_time_frame(
        ctx,
        def_val="1h",
        name="Timeframe",

):
    available_timeframes = time_frame_manager.sort_time_frames(ctx.exchange_manager.client_time_frames)
    selected_timeframe = await user_input(ctx, name, "options", def_val,
                                          options=available_timeframes)
    return selected_timeframe
