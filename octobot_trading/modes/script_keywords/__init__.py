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

from octobot_trading.modes.script_keywords import dsl
from octobot_trading.modes.script_keywords.dsl import (
    parse_quantity,
    QuantityType,
)

from octobot_trading.modes.script_keywords import basic_keywords
from octobot_trading.modes.script_keywords.basic_keywords import (
    disable_candles_plot,
    user_input,
    save_user_input,
    get_user_inputs,
    clear_user_inputs,
    get_activation_topics,
    user_select_leverage,
    user_select_emit_trading_signals,
    is_emitting_trading_signals,
    emit_trading_signals,
    set_leverage,
    set_partial_take_profit_stop_loss,
    set_plot_orders,
    store_orders,
)

from octobot_trading.modes.script_keywords import context_management
from octobot_trading.modes.script_keywords.context_management import (
    Context,
)


__all__ = [
    "parse_quantity",
    "QuantityType",
    "disable_candles_plot",
    "user_input",
    "save_user_input",
    "get_user_inputs",
    "clear_user_inputs",
    "get_activation_topics",
    "user_select_leverage",
    "user_select_emit_trading_signals",
    "is_emitting_trading_signals",
    "emit_trading_signals",
    "set_leverage",
    "set_partial_take_profit_stop_loss",
    "set_plot_orders",
    "store_orders",
    "Context",
]
