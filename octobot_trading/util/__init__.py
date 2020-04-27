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
#  License along with this library
from octobot_commons.constants import CONFIG_ENABLED_OPTION, CONFIG_CRYPTO_CURRENCIES, CONFIG_CRYPTO_PAIRS
from octobot_commons.symbol_util import split_symbol

from octobot_trading.constants import CONFIG_TRADER, CONFIG_SIMULATOR, CONFIG_TRADING, CONFIG_TRADER_REFERENCE_MARKET, \
    DEFAULT_REFERENCE_MARKET


def is_trader_enabled(config):
    return __is_trader_enabled(config, CONFIG_TRADER)


def is_trader_simulator_enabled(config):
    return __is_trader_enabled(config, CONFIG_SIMULATOR)


def __is_trader_enabled(config, trader_key):
    try:
        return config[trader_key][CONFIG_ENABLED_OPTION]
    except KeyError:
        if trader_key not in config:
            config[trader_key] = {}
        config[trader_key][CONFIG_ENABLED_OPTION] = False
        return False


def get_symbols(config):
    if CONFIG_CRYPTO_CURRENCIES in config and isinstance(config[CONFIG_CRYPTO_CURRENCIES], dict):
        for crypto_currency_data in config[CONFIG_CRYPTO_CURRENCIES].values():
            for symbol in crypto_currency_data[CONFIG_CRYPTO_PAIRS]:
                yield symbol


def get_all_currencies(config):
    currencies = set()
    for symbol in get_symbols(config):
        quote, base = split_symbol(symbol)
        currencies.add(quote)
        currencies.add(base)
    return currencies


def get_pairs(config, currency) -> []:
    pairs = []
    for symbol in get_symbols(config):
        if currency in split_symbol(symbol):
            pairs.append(symbol)
    return pairs


def get_market_pair(config, currency) -> (str, bool):
    if CONFIG_TRADING in config:
        reference_market = get_reference_market(config)
        for symbol in get_symbols(config):
            symbol_currency, symbol_market = split_symbol(symbol)
            if currency == symbol_currency and reference_market == symbol_market:
                return symbol, False
            elif reference_market == symbol_currency and currency == symbol_market:
                return symbol, True
    return "", False


def get_reference_market(config) -> str:
    # The reference market is the currency unit of the calculated quantity value
    return config[CONFIG_TRADING].get(CONFIG_TRADER_REFERENCE_MARKET, DEFAULT_REFERENCE_MARKET)
