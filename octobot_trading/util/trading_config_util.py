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
from octobot_commons.tentacles_management.class_inspector import get_deep_class_from_parent_subclasses
from octobot_tentacles_manager.api.configurator import get_activated_tentacles
from octobot_trading.modes import AbstractTradingMode


def get_activated_trading_mode(tentacles_setup_config) -> AbstractTradingMode.__class__:
    if tentacles_setup_config is not None:
        try:
            trading_modes = [tentacle_class
                             for tentacle_class in get_activated_tentacles(tentacles_setup_config)
                             if get_deep_class_from_parent_subclasses(tentacle_class, AbstractTradingMode)]

            if len(trading_modes) > 1:
                raise ConfigTradingError(
                    f"More than one activated trading mode found in your tentacle configuration, "
                    f"please activate only one")

            elif trading_modes:
                trading_mode_class = get_deep_class_from_parent_subclasses(trading_modes[0],
                                                                           AbstractTradingMode)

                if trading_mode_class is not None:
                    return trading_mode_class
        except ModuleNotFoundError as e:
            get_logger("get_activated_trading_mode").error(f"Error when loading the activated trading mode: {e}")

    raise ConfigTradingError(f"Please ensure your tentacles configuration file is valid and at least one trading "
                             f"mode is activated")
