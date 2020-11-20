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
import octobot_commons.constants as commons_constants
import octobot_commons.symbol_util as symbol_util
import octobot_trading.constants as trading_constants


def is_trader_enabled(config):
    return _is_trader_enabled(config, trading_constants.CONFIG_TRADER)


def is_trader_simulator_enabled(config):
    return _is_trader_enabled(config, trading_constants.CONFIG_SIMULATOR)


def _is_trader_enabled(config, trader_key):
    try:
        return config[trader_key][commons_constants.CONFIG_ENABLED_OPTION]
    except KeyError:
        if trader_key not in config:
            config[trader_key] = {}
        config[trader_key][commons_constants.CONFIG_ENABLED_OPTION] = False
        return False


def is_currency_enabled(config, currency, default_value) -> bool:
    return config[commons_constants.CONFIG_CRYPTO_CURRENCIES][currency].get(commons_constants.CONFIG_ENABLED_OPTION,
                                                                            default_value)


def get_symbols(config, enabled_only):
    if commons_constants.CONFIG_CRYPTO_CURRENCIES in config \
            and isinstance(config[commons_constants.CONFIG_CRYPTO_CURRENCIES], dict):
        for currency, crypto_currency_data in config[commons_constants.CONFIG_CRYPTO_CURRENCIES].items():
            if not enabled_only or is_currency_enabled(config, currency, True):
                for symbol in crypto_currency_data[commons_constants.CONFIG_CRYPTO_PAIRS]:
                    yield symbol


def get_all_currencies(config, enabled_only=False):
    currencies = set()
    for symbol in get_symbols(config, enabled_only):
        quote, base = symbol_util.split_symbol(symbol)
        currencies.add(quote)
        currencies.add(base)
    return currencies


def get_pairs(config, currency, enabled_only=False) -> []:
    pairs = []
    for symbol in get_symbols(config, enabled_only):
        if currency in symbol_util.split_symbol(symbol):
            pairs.append(symbol)
    return pairs


def get_market_pair(config, currency, enabled_only=False) -> (str, bool):
    if trading_constants.CONFIG_TRADING in config:
        reference_market = get_reference_market(config)
        for symbol in get_symbols(config, enabled_only):
            symbol_currency, symbol_market = symbol_util.split_symbol(symbol)
            if currency == symbol_currency and reference_market == symbol_market:
                return symbol, False
            elif reference_market == symbol_currency and currency == symbol_market:
                return symbol, True
    return "", False


def get_reference_market(config) -> str:
    # The reference market is the currency unit of the calculated quantity value
    return config[trading_constants.CONFIG_TRADING].get(trading_constants.CONFIG_TRADER_REFERENCE_MARKET,
                                                        trading_constants.DEFAULT_REFERENCE_MARKET)
