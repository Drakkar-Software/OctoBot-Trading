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


def entering_channel_up(price, val1, val2):
    if val1 < val2:
        return price[-1] > val1[-1] and price[-2] < val1[-2]
    if val1 > val2:
        return price[-1] > val2[-1] and price[-2] < val2[-2]


def entering_channel_down(price, val1, val2):
    if val1 > val2:
        return price[-1] < val1[-1] and price[-2] > val1[-2]
    if val1 < val2:
        return price[-1] < val2[-1] and price[-2] > val2[-2]


def entering_channel(price, val1, val2):
    if entering_channel_up(price, val1, val2):
        return True
    if entering_channel_down(price, val1, val2):
        return True


def inside_channel(price, val1, val2):
    if val1 < val2:
        return val1[-1] < price[-1] < val2[-1]
    if val1 > val2:
        return val1[-1] > price[-1] > val2[-1]


def outside_channel(price, val1, val2):
    if val1 < val2:
        return val1[-1] > price[-1] > val2[-1]
    if val1 > val2:
        return val1[-1] < price[-1] < val2[-1]
