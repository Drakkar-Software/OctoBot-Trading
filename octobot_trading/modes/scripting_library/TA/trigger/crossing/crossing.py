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
import octobot_trading.modes.scripting_library.data.reading.exchange_public_data as exchange_public_data


def crossing_up(context=None, values_to_cross=None, crossing_values=None, delay=0, max_cross_down=None, max_cross_down_lookback=5):
    # true if price just risen over value and stayed there for delay time
    condition = False
    delay = delay
    if values_to_cross is None:
        raise RuntimeError("crossing_up: you need to provide values_to_cross")
    else:
        if context is None and crossing_values is not None:
            was_below = None
            try:
                was_below = crossing_values[-delay-2] < values_to_cross[-delay-2]
            except IndexError:
                print("crossing_up: not enough values_to_cross, you need to provide same amount as delay")
            if was_below:
                for i in range(1, delay+2):
                    condition = crossing_values[-i] > values_to_cross[-i]
                    if condition is False:
                        return False
                return condition
            else:
                return False
        else:
            closes = exchange_public_data.Close(context, limit=delay+max_cross_down_lookback)
            highs = exchange_public_data.High(context, limit=delay+max_cross_down_lookback)
            lows = exchange_public_data.Low(context, limit=delay+max_cross_down_lookback)
            was_below = None
            is_currently_above = None
            try:
                was_below = lows[-delay - 2] < values_to_cross[-delay - 2]
                is_currently_above = closes[-1] > values_to_cross[-1]
            except IndexError:
                context.logger.info("crossing_up: not enough values_to_cross, you need to provide same amount as delay")
            if was_below and is_currently_above:
                for i in range(1, delay + 2):
                    condition = highs[-i] > values_to_cross[-i]
                    if condition is False:
                        return False
                return condition
            else:
                return False


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
