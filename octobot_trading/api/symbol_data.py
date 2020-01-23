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
from octobot_trading.data_manager.candles_manager import CandlesManager
from octobot_trading.data_manager.kline_manager import KlineManager
from octobot_trading.exchanges.data.exchange_symbol_data import ExchangeSymbolData
from octobot_commons.enums import TimeFrames


def get_symbol_data(exchange_manager, symbol) -> ExchangeSymbolData:
    return exchange_manager.exchange_symbols_data.get_exchange_symbol_data(symbol)


def get_symbol_candles_manager(symbol_data, time_frame) -> CandlesManager:
    return symbol_data.symbol_candles[TimeFrames(time_frame)]


def get_symbol_historical_candles(symbol_data, time_frame, limit=-1) -> dict:
    return get_symbol_candles_manager(symbol_data, time_frame).get_symbol_prices(limit)


def has_symbol_klines(symbol_data, time_frame) -> bool:
    return TimeFrames(time_frame) in symbol_data.symbol_klines


def get_symbol_klines(symbol_data, time_frame) -> list:
    return symbol_data.symbol_klines[TimeFrames(time_frame)].kline
