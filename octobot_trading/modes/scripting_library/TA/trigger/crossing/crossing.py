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


def crossing_up(price, value):
    # true if price just risen over value
    return price[-1] > value[-1] and price[-2] < value[-2]


def crossing_down(price, value):
    # true if price just fell under value
    return price[-1] < value[-1] and price[-2] > value[-2]


def crossing(price, value):
    # true if price just went below or over value
    return (price[-1] < value[-1] and price[-2] > value[-2]) or (price[-1] > value[-1] and price[-2] < value[-2])

