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


def entering_channel_up(price, val1, val2, delay=0):
    condition = False
    delay = delay + 1
    for i in range(1, delay):
        if val1 < val2:
            condition = price[-i] > val1[-i] and price[-i - 1] < val1[-i - 1]
            if not condition:
                return
        if val1 > val2:
            condition = price[-i] > val2[-i] and price[-i - 1] < val2[-i - 1]
            if not condition:
                return
    return condition


def entering_channel_down(price, val1, val2, delay=0):
    condition = False
    delay = delay + 1
    for i in range(1, delay):
        if val1 > val2:
            condition = price[-i] < val1[-i] and price[-i - 1] > val1[-i - 1]
            if not condition:
                return False
        if val1 < val2:
            condition = price[-i] < val2[-i] and price[-i - 1] > val2[-i - 1]
            if not condition:
                return False
    return condition


def entering_channel(price, val1, val2, delay=0):
    delay = delay + 1
    if entering_channel_up(price, val1, val2, delay):
        return True
    if entering_channel_down(price, val1, val2, delay):
        return True


def inside_channel(price, val1, val2, delay=0):
    condition = False
    delay = delay + 1
    for i in range(1, delay):
        if val1 < val2:
            condition = val1[-i] < price[-i] < val2[-i]
            if not condition:
                return False
        if val1 > val2:
            condition = val1[-i] > price[-i] > val2[-i]
        if not condition:
            return False
    return condition


def outside_channel(price, val1, val2, delay=0):
    condition = False
    delay = delay + 1
    for i in range(0, delay):
        if val1 < val2:
            condition = val1[-i] > price[-i] > val2[-i]
            if not condition:
                return False
        if val1 > val2:
            condition = val1[-i] < price[-i] < val2[-i]
        if not condition:
            return False
    return condition
