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
import octobot_commons.enums as common_enums
import octobot_commons.constants as common_constants
import octobot_commons.configuration as commons_configuration
import octobot_commons.tentacles_management as class_inspector

import octobot_tentacles_manager.api as configurator

import octobot_trading.enums as enums
import octobot_trading.constants as constants
import octobot_trading.modes as modes
import octobot_trading.modes.script_keywords.dsl as dsl


def get_activated_trading_mode(tentacles_setup_config):
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


def should_emit_trading_signals_user_input(trading_mode, inputs: dict):
    if trading_mode.UI.user_input(
        common_constants.CONFIG_EMIT_TRADING_SIGNALS, common_enums.UserInputTypes.BOOLEAN, False, inputs,
        title="Emit trading signals on Astrolab for people to follow.",
        order=commons_configuration.UserInput.MAX_ORDER - 2
    ):
        trading_mode.UI.user_input(
            common_constants.CONFIG_TRADING_SIGNALS_STRATEGY, common_enums.UserInputTypes.TEXT, trading_mode.get_name(),
            inputs,
            title="Name of the strategy to send signals on.",
            order=commons_configuration.UserInput.MAX_ORDER - 1,
            other_schema_values={"minLength": 0}
        )


def is_trading_signal_emitter(trading_mode) -> bool:
    """
    :return: True if the mode should be emitting trading signals according to configuration
    """
    try:
        return trading_mode.trading_config[common_constants.CONFIG_EMIT_TRADING_SIGNALS]
    except KeyError:
        return False


def _get_order_amount_title(side):
    return f"Amount per {side} order. To specify the amount per order, " \
        f"use the following syntax: " \
        f"0.1 to trade 0.1 BTC on BTC/USD, " \
        f"2{dsl.QuantityType.PERCENT.value} to trade 2% of the total portfolio value, " \
        f"12{dsl.QuantityType.AVAILABLE_PERCENT.value} to trade 12% of the available holdings, " \
        f"Leave empty to auto-compute the amount."


def user_select_order_amount(trading_mode, inputs: dict, include_buy=True, include_sell=True):
    if include_buy:
        trading_mode.UI.user_input(
                constants.CONFIG_BUY_ORDER_AMOUNT, common_enums.UserInputTypes.TEXT, "", inputs,
                title=_get_order_amount_title("buy")
        )
    if include_sell:
        trading_mode.UI.user_input(
                constants.CONFIG_SELL_ORDER_AMOUNT, common_enums.UserInputTypes.TEXT, "", inputs,
                title=_get_order_amount_title("sell")
        )


def get_user_selected_order_amount(trading_mode, side) -> str:
    try:
        if side is enums.TradeOrderSide.SELL:
            return trading_mode.trading_config[constants.CONFIG_SELL_ORDER_AMOUNT]
        if side is enums.TradeOrderSide.BUY:
            return trading_mode.trading_config[constants.CONFIG_BUY_ORDER_AMOUNT]
    except KeyError:
        return ""
    raise KeyError(f"Unknown side :{side}")
