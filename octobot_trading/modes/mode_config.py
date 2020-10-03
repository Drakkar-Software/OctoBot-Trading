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
import octobot_commons.errors as errors
import octobot_commons.logging as logging
import octobot_commons.tentacles_management as class_inspector

import octobot_tentacles_manager.api as configurator

import octobot_trading.modes as modes


def get_activated_trading_mode(tentacles_setup_config) -> modes.AbstractTradingMode.__class__:
    if tentacles_setup_config is not None:
        try:
            trading_modes = [tentacle_class
                             for tentacle_class in configurator.get_activated_tentacles(tentacles_setup_config)
                             if class_inspector.get_deep_class_from_parent_subclasses(tentacle_class,
                                                                                      modes.AbstractTradingMode)]

            if len(trading_modes) > 1:
                raise errors.ConfigTradingError(
                    f"More than one activated trading mode found in your tentacle configuration, "
                    f"please activate only one")

            elif trading_modes:
                trading_mode_class = class_inspector.get_deep_class_from_parent_subclasses(trading_modes[0],
                                                                                           modes.AbstractTradingMode)

                if trading_mode_class is not None:
                    return trading_mode_class
        except ModuleNotFoundError as e:
            logging.get_logger("get_activated_trading_mode").error(f"Error when loading "
                                                                   f"the activated trading mode: {e}")

    raise errors.ConfigTradingError(f"Please ensure your tentacles configuration file is valid and "
                                    f"at least one trading mode is activated")
