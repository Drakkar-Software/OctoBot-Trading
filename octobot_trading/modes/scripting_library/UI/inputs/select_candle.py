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

from octobot_trading.modes.scripting_library.data.reading.exchange_public_data import Open, High, Low, Close, Volume, hl2, hlc3, ohlc4
from .user_inputs import user_input


async def user_select_candle(
        ctx,
        name="Select Candle Source",
        def_val="close",
        time_frame=None,
        symbol=None,
        limit=-1,
        enable_volume=True,
        return_source_name=False,
        max_history=False,
):
    available_data_src = ["open", "high", "low", "close", "hl2", "hlc3", "ohlc4"]
    if enable_volume:
        available_data_src.append("volume")

    data_source = await user_input(ctx, name, "options", def_val, options=available_data_src)
    symbol = symbol or ctx.symbol
    time_frame = time_frame or ctx.time_frame
    candle_source = None
    if data_source == "close":
        candle_source = await Close(ctx, symbol, time_frame, limit, max_history)
    elif data_source == "open":
        candle_source = await Open(ctx, symbol, time_frame, limit, max_history)
    elif data_source == "high":
        candle_source = await High(ctx, symbol, time_frame, limit, max_history)
    elif data_source == "low" and enable_volume:
        candle_source = await Low(ctx, symbol, time_frame, limit, max_history)
    elif data_source == "volume":
        candle_source = await Volume(ctx, symbol, time_frame, limit, max_history)
    elif data_source == "hl2":
        candle_source = await hl2(ctx, symbol, time_frame, limit, max_history)
    elif data_source == "hlc3":
        candle_source = await hlc3(ctx, symbol, time_frame, limit, max_history)
    elif data_source == "ohlc4":
        candle_source = await ohlc4(ctx, symbol, time_frame, limit, max_history)
    if return_source_name:
        return candle_source, data_source
    else:
        return candle_source
