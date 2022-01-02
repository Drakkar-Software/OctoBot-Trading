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
import octobot_commons.enums as commons_enums
import octobot_trading.api as api
import octobot_trading.constants as trading_constants
import octobot_trading.personal_data as personal_data
import octobot_trading.exchange_data as exchange_data


# real time in live mode
# lowest available candle time on backtesting
def current_live_time(context) -> float:
    return api.get_exchange_current_time(context.exchange_manager)


async def current_candle_time(context, symbol=None, time_frame=None):
    symbol = symbol or context.symbol
    time_frame = time_frame or context.time_frame
    return (await Time(context, symbol, time_frame, limit=1))[-1]  # todo is there a more efficient way?


# Use capital letters to avoid python native lib conflicts
async def Time(context, symbol=None, time_frame=None, limit=-1, max_history=False):
    candles_manager = await _get_candle_manager(context, symbol, time_frame, max_history)
    return candles_manager.get_symbol_time_candles(-1 if max_history else limit)


# real time in live mode
# lowest available candle closes on backtesting
async def current_live_price(context, symbol=None):
    return await personal_data.get_up_to_date_price(context.exchange_manager, symbol or context.symbol,
                                                    timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT,
                                                    base_error="Can't get the current price:")


async def current_candle_price(context, symbol=None, time_frame=None):
    candles_manager = await _get_candle_manager(context, symbol, time_frame, False)
    return candles_manager.get_symbol_close_candles(1)[-1]  # todo more efficient way?


# Use capital letters to avoid python native lib conflicts
async def Open(context, symbol=None, time_frame=None, limit=-1, max_history=False):
    candles_manager = await _get_candle_manager(context, symbol, time_frame, max_history)
    return candles_manager.get_symbol_open_candles(-1 if max_history else limit)


# Use capital letters to avoid python native lib conflicts
async def High(context, symbol=None, time_frame=None, limit=-1, max_history=False):
    candles_manager = await _get_candle_manager(context, symbol, time_frame, max_history)
    return candles_manager.get_symbol_high_candles(-1 if max_history else limit)


# Use capital letters to avoid python native lib conflicts
async def Low(context, symbol=None, time_frame=None, limit=-1, max_history=False):
    candles_manager = await _get_candle_manager(context, symbol, time_frame, max_history)
    return candles_manager.get_symbol_low_candles(-1 if max_history else limit)


# Use capital letters to avoid python native lib conflicts
async def Close(context, symbol=None, time_frame=None, limit=-1, max_history=False):
    candles_manager = await _get_candle_manager(context, symbol, time_frame, max_history)
    return candles_manager.get_symbol_close_candles(-1 if max_history else limit)


async def hl2(context, symbol=None, time_frame=None, limit=-1, max_history=False):
    try:
        from tentacles.Evaluator.Util.candles_util import CandlesUtil
        candles_manager = await _get_candle_manager(context, symbol, time_frame, max_history)
        return CandlesUtil.HL2(
            candles_manager.get_symbol_high_candles(-1 if max_history else limit),
            candles_manager.get_symbol_low_candles(-1 if max_history else limit)
        )
    except ImportError:
        raise RuntimeError("CandlesUtil tentacle is required to use HL2")


async def hlc3(context, symbol=None, time_frame=None, limit=-1, max_history=False):
    try:
        from tentacles.Evaluator.Util.candles_util import CandlesUtil
        candles_manager = await _get_candle_manager(context, symbol, time_frame, max_history)
        return CandlesUtil.HLC3(
            candles_manager.get_symbol_high_candles(-1 if max_history else limit),
            candles_manager.get_symbol_low_candles(-1 if max_history else limit),
            candles_manager.get_symbol_close_candles(-1 if max_history else limit)
        )
    except ImportError:
        raise RuntimeError("CandlesUtil tentacle is required to use HLC3")


async def ohlc4(context, symbol=None, time_frame=None, limit=-1, max_history=False):
    try:
        from tentacles.Evaluator.Util.candles_util import CandlesUtil
        candles_manager = await _get_candle_manager(context, symbol, time_frame, max_history)
        return CandlesUtil.HLC3(
            candles_manager.get_symbol_open_candles(-1 if max_history else limit),
            candles_manager.get_symbol_high_candles(-1 if max_history else limit),
            candles_manager.get_symbol_low_candles(-1 if max_history else limit),
            candles_manager.get_symbol_close_candles(-1 if max_history else limit)
        )
    except ImportError:
        raise RuntimeError("CandlesUtil tentacle is required to use OHLC4")


# Use capital letters to avoid python native lib conflicts
async def Volume(context, symbol=None, time_frame=None, limit=-1, max_history=False):
    candles_manager = await _get_candle_manager(context, symbol, time_frame, max_history)
    return candles_manager.get_symbol_volume_candles(-1 if max_history else limit)

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


async def _local_candles_manager(exchange_manager, symbol, time_frame):
    # warning: should only be called with an exchange simulator (in backtesting)
    candles_manager = exchange_data.CandlesManager()
    ohlcv_data: list = await exchange_manager.exchange.exchange_importers[0].get_ohlcv(
        exchange_name=exchange_manager.exchange_name,
        symbol=symbol,
        time_frame=commons_enums.TimeFrames(time_frame))
    chronological_candles = sorted(ohlcv_data, key=lambda candle: candle[0])
    full_candles_history = [ohlcv[-1] for ohlcv in chronological_candles]
    candles_manager.MAX_CANDLES_COUNT = len(full_candles_history)
    await candles_manager.initialize()
    candles_manager.replace_all_candles(full_candles_history)
    return candles_manager


async def _get_candle_manager(context, symbol, time_frame, max_history):
    symbol = symbol or context.symbol
    time_frame = time_frame or context.time_frame
    if max_history and context.exchange_manager.is_backtesting:
        return await _local_candles_manager(context.exchange_manager, symbol, time_frame)
    return api.get_symbol_candles_manager(api.get_symbol_data(context.exchange_manager, symbol, allow_creation=False),
                                          time_frame)
