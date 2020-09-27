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
import octobot_trading
from octobot_commons.constants import CONFIG_ENABLED_OPTION


def is_trader_enabled(config):
    return _is_trader_enabled(config, octobot_trading.CONFIG_TRADER)


def is_trader_simulator_enabled(config):
    return _is_trader_enabled(config, octobot_trading.CONFIG_SIMULATOR)


def _is_trader_enabled(config, trader_key):
    try:
        return config[trader_key][CONFIG_ENABLED_OPTION]
    except KeyError:
        if trader_key not in config:
            config[trader_key] = {}
        config[trader_key][CONFIG_ENABLED_OPTION] = False
        return False
