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
from octobot_commons.errors import ConfigTradingError
from octobot_commons.logging.logging_util import get_logger
from octobot_commons.tentacles_management import create_classes_list
from octobot_commons.tentacles_management.config_manager import reload_tentacle_config

from octobot_trading.api import LOGGER_TAG
from octobot_trading.constants import CONFIG_TRADING_TENTACLES
from octobot_trading.modes import AbstractTradingMode
from octobot_trading.util.trading_config_util import get_activated_trading_mode as util_get_activated_trading_mode


def init_trading_mode_config(config, trading_tentacles_path) -> None:
    reload_tentacle_config(config, CONFIG_TRADING_TENTACLES, trading_tentacles_path, ConfigTradingError)
    create_classes_list(config, AbstractTradingMode)


def get_activated_trading_mode(config) -> AbstractTradingMode:
    return util_get_activated_trading_mode(config)


def get_trading_config(config) -> dict:
    return config[CONFIG_TRADING_TENTACLES]


async def create_trading_mode(config, exchange_manager) -> None:
    try:
        trading_mode = util_get_activated_trading_mode(config)(config, exchange_manager)
        await trading_mode.initialize()
        get_logger(f"{LOGGER_TAG}[{exchange_manager.exchange.name}]")\
            .debug(f"Using {trading_mode.get_name()} trading mode")
    except RuntimeError as e:
        get_logger(LOGGER_TAG).error(e.args[0])
        raise e
