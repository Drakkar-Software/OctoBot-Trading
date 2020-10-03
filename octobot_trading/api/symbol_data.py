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
import octobot_trading.enums
import octobot_trading.exchanges as exchanges
import octobot_trading.exchange_data as exchange_data
import octobot_commons.enums as enums


def get_symbol_data(exchange_manager, symbol, allow_creation=True) -> ExchangeSymbolData:
    return exchange_manager.exchange_symbols_data.get_exchange_symbol_data(symbol, allow_creation=allow_creation)


def get_symbol_candles_manager(symbol_data, time_frame) -> CandlesManager:
    return symbol_data.symbol_candles[TimeFrames(time_frame)]


def get_symbol_historical_candles(symbol_data, time_frame, limit=-1) -> object:
    return get_symbol_candles_manager(symbol_data, time_frame).get_symbol_prices(limit)


def get_candle_as_list(candles_arrays, candle_index=0) -> list:
    return adapter_get_candle_as_list(candles_arrays, candle_index)


def has_symbol_klines(symbol_data, time_frame) -> bool:
    return TimeFrames(time_frame) in symbol_data.symbol_klines


def get_symbol_klines(symbol_data, time_frame) -> list:
    return symbol_data.symbol_klines[TimeFrames(time_frame)].kline


def get_symbol_close_candles(symbol_data, time_frame, limit=-1, include_in_construction=False):
    return adapter_get_symbol_close_candles(symbol_data, time_frame, limit, include_in_construction)


def get_symbol_open_candles(symbol_data, time_frame, limit=-1, include_in_construction=False):
    return adapter_get_symbol_open_candles(symbol_data, time_frame, limit, include_in_construction)


def get_symbol_high_candles(symbol_data, time_frame, limit=-1, include_in_construction=False):
    return adapter_get_symbol_high_candles(symbol_data, time_frame, limit, include_in_construction)


def get_symbol_low_candles(symbol_data, time_frame, limit=-1, include_in_construction=False):
    return adapter_get_symbol_low_candles(symbol_data, time_frame, limit, include_in_construction)


def get_symbol_volume_candles(symbol_data, time_frame, limit=-1, include_in_construction=False):
    return adapter_get_symbol_volume_candles(symbol_data, time_frame, limit, include_in_construction)


def get_symbol_time_candles(symbol_data, time_frame, limit=-1, include_in_construction=False):
    return adapter_get_symbol_time_candles(symbol_data, time_frame, limit, include_in_construction)


def create_new_candles_manager(candles=None) -> CandlesManager:
    manager = CandlesManager()
    if candles is not None:
        manager.replace_all_candles(candles)
    return manager


def force_set_mark_price(exchange_manager, symbol, price):
    exchange_manager.exchange_symbols_data.get_exchange_symbol_data(symbol).prices_manager.\
        set_mark_price(price, MarkPriceSources.EXCHANGE_MARK_PRICE.value)


def is_mark_price_initialized(exchange_manager, symbol: str) -> bool:
    return exchange_manager.exchange_symbols_data.get_exchange_symbol_data(symbol).prices_manager.\
        valid_price_received_event.is_set()
