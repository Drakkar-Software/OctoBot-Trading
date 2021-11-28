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

import tulipy as ti
from octobot_trading.modes.scripting_library.orders.offsets import get_offset


def moving_up(price, moving, bars):
    if (price[-1] - ti.min(price, bars)) > get_offset(moving):
        return True


def moving_down(price, moving, bars):
    if (ti.max(price, bars) - price[-1]) > get_offset(moving):
        return True
