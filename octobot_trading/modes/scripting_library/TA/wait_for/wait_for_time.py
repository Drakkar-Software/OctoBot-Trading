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

import asyncio
import octobot_commons.enums as commons_enums


async def wait_for_time(delay):
    await asyncio.sleep(delay)


async def wait_for_bars(
        timeframe=None,
        bars=None
):
    # see https://github.com/Drakkar-Software/OctoBot-Commons/blob/master/octobot_commons/enums.py#L19
    time_frame = commons_enums.TimeFrames(timeframe)
    minutes = commons_enums.TimeFramesMinutes[time_frame]
    delay_seconds = minutes * 60 * bars
    await asyncio.sleep(delay_seconds)
