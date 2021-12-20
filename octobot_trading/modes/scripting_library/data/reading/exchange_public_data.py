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
import octobot_trading.constants as trading_constants
import octobot_trading.personal_data as personal_data


# real time in live mode
# lowest available candle time on backtesting
def current_live_time(context) -> float:
    return api.get_exchange_current_time(context.exchange_manager)


def current_candle_time(context, symbol=None, time_frame=None):
    symbol = symbol or context.symbol
    time_frame = time_frame or context.time_frame
    return Time(context, symbol, time_frame, limit=1)[-1]  # todo is there a more efficient way?


# Use capital letters to avoid python native lib conflicts
def Time(context, symbol=None, time_frame=None, limit=-1):
    symbol = symbol or context.symbol
    time_frame = time_frame or context.time_frame
    return _get_candle_manager(context.exchange_manager, symbol, time_frame).get_symbol_time_candles(limit)


# real time in live mode
# lowest available candle closes on backtesting
async def current_live_price(context, symbol=None):
    return await personal_data.get_up_to_date_price(context.exchange_manager, symbol or context.symbol,
                                                    timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT,
                                                    base_error="Can't get the current price:")


def current_candle_price(context, symbol=None, time_frame=None):
    symbol = symbol or context.symbol
    time_frame = time_frame or context.time_frame
    return _get_candle_manager(context.exchange_manager, symbol, time_frame).get_symbol_close_candles(1)[-1]  # todo more efficient way?


# Use capital letters to avoid python native lib conflicts
def Open(context, symbol=None, time_frame=None, limit=-1):
    symbol = symbol or context.symbol
    time_frame = time_frame or context.time_frame
    return _get_candle_manager(context.exchange_manager, symbol, time_frame).get_symbol_open_candles(limit)

# Use capital letters to avoid python native lib conflicts
def High(context, symbol=None, time_frame=None, limit=-1):
    symbol = symbol or context.symbol
    time_frame = time_frame or context.time_frame
    return _get_candle_manager(context.exchange_manager, symbol, time_frame).get_symbol_high_candles(limit)

# Use capital letters to avoid python native lib conflicts
def Low(context, symbol=None, time_frame=None, limit=-1):
    symbol = symbol or context.symbol
    time_frame = time_frame or context.time_frame
    return _get_candle_manager(context.exchange_manager, symbol, time_frame).get_symbol_low_candles(limit)

# Use capital letters to avoid python native lib conflicts
def Close(context, symbol=None, time_frame=None, limit=-1):
    symbol = symbol or context.symbol
    time_frame = time_frame or context.time_frame
    return _get_candle_manager(context.exchange_manager, symbol, time_frame).get_symbol_close_candles(limit)


def hl2(context, symbol=None, time_frame=None, limit=-1):
    try:
        from tentacles.Evaluator.Util.candles_util import CandlesUtil
        symbol = symbol or context.symbol
        time_frame = time_frame or context.time_frame
        return CandlesUtil.HL2(High(context, symbol, time_frame, limit), Low(context, symbol, time_frame, limit))
    except ImportError:
        raise RuntimeError("CandlesUtil tentacle is required to use HL2")

def hlc3(context, symbol=None, time_frame=None, limit=-1):
    try:
        from tentacles.Evaluator.Util.candles_util import CandlesUtil
        symbol = symbol or context.symbol
        time_frame = time_frame or context.time_frame
        return CandlesUtil.HLC3(High(context, symbol, time_frame, limit),
                                Low(context, symbol, time_frame, limit),
                                Close(context, symbol, time_frame, limit))
    except ImportError:
        raise RuntimeError("CandlesUtil tentacle is required to use HLC3")

def ohlc4(context, symbol=None, time_frame=None, limit=-1):
    try:
        from tentacles.Evaluator.Util.candles_util import CandlesUtil
        symbol = symbol or context.symbol
        time_frame = time_frame or context.time_frame
        return CandlesUtil.OHLC4(Open(context, symbol, time_frame, limit),
                                 High(context, symbol, time_frame, limit),
                                 Low(context, symbol, time_frame, limit),
                                 Close(context, symbol, time_frame, limit))
    except ImportError:
        raise RuntimeError("CandlesUtil tentacle is required to use OHLC4")

# Use capital letters to avoid python native lib conflicts
def Volume(context, symbol=None, time_frame=None):
    symbol = symbol or context.symbol
    time_frame = time_frame or context.time_frame
    return _get_candle_manager(context.exchange_manager, symbol, time_frame).get_symbol_volume_candles()

# def buy_volume():
#         var=0 #todo
#
# def sell_volume():
#     var = 0 # todo
#
# def orderbook():
#     var = 0 # todo
#
# def openinterest():
#     var = 00 # todo
#
# def long_short_ratio():
#     var = 0 # todo
#
# def tick_data():
#     var = 0 # todo

def _get_candle_manager(exchange_manager, symbol, time_frame):
    return api.get_symbol_candles_manager(api.get_symbol_data(exchange_manager, symbol, allow_creation=False),
                                          time_frame)
