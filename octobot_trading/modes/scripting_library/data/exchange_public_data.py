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


import octobot_trading.api as api
import asyncio
import octobot_trading.constants as trading_constants


async def current_price(pair, exchange_manager):
    try:
        return await exchange_manager.exchange_symbols_data.get_exchange_symbol_data(pair) \
            .prices_manager.get_mark_price(timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT)
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError("Mark price is not available")


def current_time(context) -> float:
    return api.get_exchange_current_time(context.exchange_manager)


# Use capital letters to avoid python native lib conflicts
def Open(context, symbol, time_frame):
    return _get_candle_manager(context.exchange_manager, symbol, time_frame).get_symbol_open_candles()

# Use capital letters to avoid python native lib conflicts
def High(context, symbol, time_frame):
    return _get_candle_manager(context.exchange_manager, symbol, time_frame).get_symbol_high_candles()

# Use capital letters to avoid python native lib conflicts
def Low(context, symbol, time_frame):
    return _get_candle_manager(context.exchange_manager, symbol, time_frame).get_symbol_low_candles()

# Use capital letters to avoid python native lib conflicts
def Close(context, symbol, time_frame):
    return _get_candle_manager(context.exchange_manager, symbol, time_frame).get_symbol_close_candles()

# Use capital letters to avoid python native lib conflicts
def Time(context, symbol, time_frame):
    return _get_candle_manager(context.exchange_manager, symbol, time_frame).get_symbol_time_candles()

def hl2(exchange_manager, symbol, time_frame):
    return # todo merge open high low into one array -

def ohl3(exchange_manager, symbol, time_frame):
    return # todo merge open high low into one array

def ohlc4(exchange_manager, symbol, time_frame):
    return # todo merge open high low into one array

# Use capital letters to avoid python native lib conflicts
def Volume(context, symbol, time_frame):
    return _get_candle_manager(context.exchange_manager, symbol, time_frame).get_symbol_volume_candles()

def buy_volume():
        var=0 #todo

def sell_volume():
    var = 0 # todo

def orderbook():
    var = 0 # todo

def openinterest():
    var = 00 # todo

def long_short_ratio():
    var = 0 # todo

def tick_data():
    var = 0 # todo

def _get_candle_manager(exchange_manager, symbol, time_frame):
    return api.get_symbol_candles_manager(api.get_symbol_data(exchange_manager, symbol), time_frame)
