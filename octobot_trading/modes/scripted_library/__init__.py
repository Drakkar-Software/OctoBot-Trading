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

from octobot_trading.modes.scripted_library import basic_keywords
from octobot_trading.modes.scripted_library.basic_keywords import (
    user_input,
    save_user_input,
    get_user_inputs,
    clear_user_inputs,
    get_activation_topics,
    user_select_leverage,
    set_leverage,
    set_partial_take_profit_stop_loss,
    set_plot_orders,
    store_orders,
    store_trade,
    store_transactions,
    save_metadata,
    save_portfolio,
    clear_run_data,
    clear_orders_cache,
    clear_trades_cache,
    clear_transactions_cache,
    clear_all_tables,
)

from octobot_trading.modes.scripted_library import context_management
from octobot_trading.modes.scripted_library.context_management import (
    Context,
)


__all__ = [
    "user_input",
    "save_user_input",
    "get_user_inputs",
    "clear_user_inputs",
    "get_activation_topics",
    "user_select_leverage",
    "set_leverage",
    "set_partial_take_profit_stop_loss",
    "set_plot_orders",
    "store_orders",
    "store_trade",
    "store_transactions",
    "save_metadata",
    "save_portfolio",
    "clear_run_data",
    "clear_orders_cache",
    "clear_trades_cache",
    "clear_transactions_cache",
    "clear_all_tables",
    "Context",
]
