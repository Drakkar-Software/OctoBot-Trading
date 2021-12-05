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


def crossing_up(price, value, delay=0):
    # true if price just risen over value and stayed there for delay time
    condition = False
    delay = delay + 2
    for i in range(1, delay):
        condition = price[-i] > value[-i] and price[-i-1] < value[-i-1]
        if condition is False:
            return False
    return condition


def crossing_down(price, value, delay=0):
    # true if price just fell under value and stayed there for delay time
    condition = False
    delay = delay + 2
    for i in range(1, delay):
        condition = price[-i] < value[-i] and price[-i-1] > value[-i-1]
        if condition is False:
            return False
    return condition


def crossing(price, value, delay=0):
    # true if price just went below or over value and stayed there for delay time
    condition = False
    delay = delay + 2
    for i in range(1, delay):
        condition = (price[-i] < value[-i] and price[-i-1] > value[-i-1]) or (price[-i] > value[-i] and price[-i-1] < value[-i-1])
        if condition is None:
            return False
    return condition
