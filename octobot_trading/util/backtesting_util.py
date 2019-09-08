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
import os

from octobot_commons.constants import CONFIG_ENABLED_OPTION
from octobot_commons.symbol_util import split_symbol

from octobot_trading.constants import CONFIG_TRADING, CONFIG_SIMULATOR, \
    CONFIG_STARTING_PORTFOLIO, CONFIG_CRYPTO_CURRENCIES, CONFIG_BACKTESTING, \
    CONFIG_BACKTESTING_DATA_FILES, DEFAULT_REFERENCE_MARKET, BACKTESTING_FILE_PATH, CONFIG_CRYPTO_PAIRS, CONFIG_TRADER, \
    CONFIG_TRADER_REFERENCE_MARKET, CONFIG_BACKTESTING_OTHER_MARKETS_STARTING_PORTFOLIO
from octobot_trading.exchanges.backtesting.collector.data_file_manager import interpret_file_name, is_valid_ending


def initialize_backtesting(config, data_files):
    __add_config_default_backtesting_values(config)
    config[CONFIG_CRYPTO_CURRENCIES] = {}
    config[CONFIG_BACKTESTING][CONFIG_BACKTESTING_DATA_FILES] = []
    ignored_files = []
    reference_market = __get_reference_market(data_files)
    if DEFAULT_REFERENCE_MARKET != reference_market:
        __switch_reference_market(config, reference_market)
    if data_files:
        for data_file_to_use in data_files:
            _, file_symbol, _, _ = interpret_file_name(data_file_to_use)
            currency, _ = split_symbol(file_symbol)
            full_file_path = os.path.join(BACKTESTING_FILE_PATH, data_file_to_use)
            ending = f".{full_file_path.split('.')[-1]}"
            full_file_path += full_file_path if not is_valid_ending(ending) else ""
            if currency not in config[CONFIG_CRYPTO_CURRENCIES]:
                config[CONFIG_CRYPTO_CURRENCIES][currency] = {CONFIG_CRYPTO_PAIRS: []}
            if file_symbol not in config[CONFIG_CRYPTO_CURRENCIES][currency][CONFIG_CRYPTO_PAIRS]:
                config[CONFIG_CRYPTO_CURRENCIES][currency][CONFIG_CRYPTO_PAIRS].append(file_symbol)
                config[CONFIG_BACKTESTING][CONFIG_BACKTESTING_DATA_FILES].append(full_file_path)
            else:
                ignored_files.append(data_file_to_use)

    return ignored_files


def __add_config_default_backtesting_values(config):
    if CONFIG_BACKTESTING not in config:
        config[CONFIG_BACKTESTING] = {}
    config[CONFIG_BACKTESTING][CONFIG_ENABLED_OPTION] = True
    config[CONFIG_TRADER][CONFIG_ENABLED_OPTION] = False
    config[CONFIG_SIMULATOR][CONFIG_ENABLED_OPTION] = True


def __switch_reference_market(config_to_use, market):
    config_to_use[CONFIG_TRADING][CONFIG_TRADER_REFERENCE_MARKET] = market
    config_to_use[CONFIG_SIMULATOR][CONFIG_STARTING_PORTFOLIO][market] = \
        CONFIG_BACKTESTING_OTHER_MARKETS_STARTING_PORTFOLIO


def __get_reference_market(data_files):
    reference_market = None
    for data_file in data_files:
        _, file_symbol, _, _ = interpret_file_name(data_file)
        currency, market = split_symbol(file_symbol)
        if reference_market is None:
            reference_market = market
        elif not reference_market == market:
            # more than one reference market in data_files: use first reference market
            return reference_market
    return reference_market if reference_market is not None else DEFAULT_REFERENCE_MARKET
