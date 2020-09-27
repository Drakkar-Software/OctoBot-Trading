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
from octobot_commons.constants import CONFIG_CRYPTO_CURRENCIES, CONFIG_CRYPTO_PAIRS
from octobot_commons.symbol_util import split_symbol

import octobot_trading
from octobot_trading.util import initializable
from octobot_trading.util import trading_config_util
from octobot_trading.util.initializable import (Initializable, )
from octobot_trading.util.trading_config_util import (get_activated_trading_mode, )


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
    if octobot_trading.CONFIG_TRADING in config:
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
    return config[octobot_trading.CONFIG_TRADING].get(octobot_trading.CONFIG_TRADER_REFERENCE_MARKET,
                                                      octobot_trading.DEFAULT_REFERENCE_MARKET)


__all__ = ['Initializable', 'get_activated_trading_mode', 'initializable', 'trading_config_util',
           'get_symbols', 'get_all_currencies', 'get_pairs', 'get_market_pair', 'get_reference_market']
