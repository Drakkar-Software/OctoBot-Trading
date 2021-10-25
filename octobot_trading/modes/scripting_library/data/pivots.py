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


# idea: calculate pivot highs/lows on multiple timeframes and cache them in the database (caching should be easily available for usage on other data)

def major_pivots(pair, timeframes, side="all", length=500):

    for timeframe in timeframes:
        selected_highs = High(pair, timeframe) # todo pair
        selected_lows = Low(pair, timeframe) # todo pair

        pivot_highs = (selected_highs[n-2] < selected_highs[n]) and (selected_highs[n-1] < selected_highs[n]) and (selected_highs[n+1] < selected_highs[n]) and (selected_highs[n+2] < selected_highs[n])
        pivot_lows = (selected_lows[n-2] > selected_lows[n]) and (selected_lows[n-1] > selected_lows[n]) and (selected_lows[n+1] > selected_lows[n]) and (selected_lows[n+2] > selected_lows[n])

        # todo merge both sides and cache them in the db
        #  mark them as major and add timeframes to list and a counter for on how many timframes its the same pivot
        return pivot_lows + pivot_highs


def pivots(pair, timeframes, side="all", length=500):
    for timeframe in timeframes:
        selected_highs = High(pair, timeframe)  # todo pair
        selected_lows = Low(pair, timeframe)  # todo pair
        pivot_highs = (selected_highs[n-1] < selected_highs[n]) and (selected_highs[n+1] < selected_highs[n])
        pivot_lows = (selected_lows[n-1] > selected_lows[n]) and (selected_lows[n+1] > selected_lows[n])

        # todo merge both sides and cache them in the db
        #  mark them as major and add timeframes to list and a counter for on how many timframes its the same pivot
        return pivot_lows + pivot_highs
