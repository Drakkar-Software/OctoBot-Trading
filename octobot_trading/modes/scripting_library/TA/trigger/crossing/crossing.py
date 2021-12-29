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
import octobot_trading.modes.scripting_library.orders.offsets.offset as offset
import tulipy as ti


async def crossing_up(context=None, values_to_cross=None, crossing_values=None, delay=0, max_cross_down=None, max_cross_down_lookback=5):
    # true if price just risen over value and stayed there for delay time
    condition = False
    delay = delay
    if values_to_cross is None:
        raise RuntimeError("crossing_up: you need to provide values_to_cross")
    else:
        if crossing_values is not None:
            was_below = None
            try:
                was_below = crossing_values[-delay-2] < values_to_cross[-delay-2]
            except IndexError:
                context.logger.info("crossing_up: not enough values_to_cross, length needs to be same as delay")
                return None

            didnt_cross_to_much = True
            if max_cross_down:
                try:
                    didnt_cross_to_much = min(values_to_cross[-max_cross_down_lookback:]) \
                                          - float(await offset.get_offset(context, "-" + max_cross_down)) \
                                          < min(crossing_values[-max_cross_down_lookback:])
                except ValueError:
                    context.logger.info("crossing_up: not enough values_to_cross, length needs to be same "
                                        "as max_cross_down_lookback")
                    return None

            if was_below and didnt_cross_to_much:
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
                context.logger.info("crossing_up: not enough values_to_cross, length needs to be same as delay")
                return None

            didnt_cross_to_much = True
            if max_cross_down is not None:
                try:
                    didnt_cross_to_much = min(values_to_cross[-max_cross_down_lookback:]) \
                                          - float(await offset.get_offset(context, "-" + max_cross_down)) \
                                          < min(lows[-max_cross_down_lookback:])
                except ValueError:
                    context.logger.info("crossing_up: not enough values_to_cross, length needs to be same "
                                        "as max_cross_down_lookback")
                    return None

            if was_below and is_currently_above and didnt_cross_to_much:
                for i in range(1, delay + 2):
                    condition = highs[-i] > values_to_cross[-i]
                    if condition is False:
                        return False
                return condition
            else:
                return False


async def crossing_down(context=None, values_to_cross=None, crossing_values=None, delay=0, max_cross_up=None, max_cross_up_lookback=5):
    # true if price just fell under value and stayed there for delay time
    condition = False
    delay = delay
    if values_to_cross is None:
        raise RuntimeError("crossing_down: you need to provide values_to_cross")
    else:
        if crossing_values is not None:
            was_above = None
            try:
                was_above = crossing_values[-delay - 2] < values_to_cross[-delay - 2]
            except IndexError:
                context.logger.info("crossing_down: not enough values_to_cross, length needs to be same as delay")
                return None


            didnt_cross_to_much = True
            if max_cross_up is not None:
                try:
                    didnt_cross_to_much = max(values_to_cross[-max_cross_up_lookback:]) \
                                          + float(await offset.get_offset(context, "-" + max_cross_up)) \
                                          > max(crossing_values[-max_cross_up_lookback:])
                except ValueError:
                    context.logger.info("crossing_down: not enough values_to_cross, length needs to be same "
                                        "as max_cross_up_lookback")
                    return None

            if was_above and didnt_cross_to_much:
                for i in range(1, delay + 2):
                    condition = crossing_values[-i] < values_to_cross[-i]
                    if condition is False:
                        return False
                return condition
            else:
                return False
        else:
            closes = exchange_public_data.Close(context, limit=delay + max_cross_up_lookback)
            highs = exchange_public_data.High(context, limit=delay + max_cross_up_lookback)
            lows = exchange_public_data.Low(context, limit=delay + max_cross_up_lookback)
            was_above = None
            is_currently_above = None
            try:
                was_above = highs[-delay - 2] > values_to_cross[-delay - 2]
                is_currently_above = closes[-1] < values_to_cross[-1]
            except IndexError:
                context.logger.info("crossing_down: not enough values_to_cross, length needs to be same as delay")
                return None

            didnt_cross_to_much = True
            if max_cross_up:
                try:
                    didnt_cross_to_much = max(values_to_cross[-max_cross_up_lookback:])  \
                                          - float(await offset.get_offset(context, max_cross_up)) \
                                          < max(highs[-max_cross_up_lookback:])
                except ValueError:
                    context.logger.info("crossing_down: not enough values_to_cross, length needs to be same "
                                        "as max_cross_up_lookback")
                    return None

            if was_above and is_currently_above and didnt_cross_to_much:
                for i in range(1, delay + 2):
                    condition = lows[-i] < values_to_cross[-i]
                    if condition is False:
                        return False
                return condition
            else:
                return False


async def crossing(context=None, values_to_cross=None, crossing_values=None, delay=0, max_cross_up=None, max_cross_up_lookback=5):
    # true if price just went below or over value and stayed there for delay time and didnt cross to much
    c_up = await crossing_up(context, values_to_cross, crossing_values, delay, max_cross_up, max_cross_up_lookback)
    if c_up:
        return True
    c_down = await crossing_down(context, values_to_cross, crossing_values, delay, max_cross_up, max_cross_up_lookback)
    return c_down
