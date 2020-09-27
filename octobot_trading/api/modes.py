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

import octobot_trading.modes as modes
import octobot_trading.util as util


def get_trading_modes(exchange_manager) -> list:
    return exchange_manager.trading_modes


def get_trading_mode_symbol(trading_mode) -> list:
    return trading_mode.symbol


def get_trading_mode_current_state(trading_mode) -> tuple:
    return trading_mode.get_current_state()


def get_activated_trading_mode(tentacles_setup_config) -> modes.AbstractTradingMode.__class__:
    return util.get_activated_trading_mode(tentacles_setup_config)
