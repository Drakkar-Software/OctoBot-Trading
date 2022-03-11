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

from octobot_trading.api import symbol_data
from octobot_trading.api import trades
from octobot_trading.api import channels
from octobot_trading.api import exchange
from octobot_trading.api import modes
from octobot_trading.api import trader
from octobot_trading.api import portfolio
from octobot_trading.api import profitability
from octobot_trading.api import orders

from octobot_trading.api.symbol_data import (
    get_symbol_data,
    get_symbol_candles_manager,
    get_symbol_historical_candles,
    are_symbol_candles_initialized,
    get_candle_as_list,
    has_symbol_klines,
    get_symbol_klines,
    get_symbol_candles_count,
    get_symbol_close_candles,
    get_symbol_open_candles,
    get_symbol_high_candles,
    get_symbol_low_candles,
    get_symbol_volume_candles,
    get_symbol_time_candles,
    create_new_candles_manager,
    force_set_mark_price,
    is_mark_price_initialized,
)
from octobot_trading.api.trades import (
    get_trade_history,
    get_total_paid_trading_fees,
    get_trade_exchange_name,
    parse_trade_type,
    trade_to_dict,
    get_win_rate,
)
from octobot_trading.api.channels import (
    subscribe_to_ohlcv_channel,
    subscribe_to_trades_channel,
    subscribe_to_order_channel,
)
from octobot_trading.api.exchange import (
    create_exchange_builder,
    get_exchange_configurations_from_exchange_name,
    get_exchange_manager_from_exchange_name_and_id,
    get_exchange_available_time_frames,
    get_exchange_available_required_time_frames,
    get_exchange_configuration_from_exchange_id,
    get_exchange_manager_from_exchange_id,
    get_exchange_managers_from_exchange_ids,
    get_trading_exchanges,
    is_exchange_trading,
    get_exchange_manager_id,
    get_exchange_manager_is_sandboxed,
    get_exchange_current_time,
    get_exchange_allowed_time_lag,
    get_exchange_id_from_matrix_id,
    get_matrix_id_from_exchange_id,
    get_all_exchange_ids_from_matrix_id,
    get_exchange_configuration_from_exchange,
    get_all_exchange_ids_with_same_matrix_id,
    get_exchange_names,
    get_exchange_ids,
    get_exchange_name,
    has_only_ohlcv,
    get_is_backtesting,
    get_backtesting_data_files,
    get_backtesting_data_file,
    get_has_websocket,
    supports_websockets,
    is_compatible_account,
    is_sponsoring,
    is_valid_account,
    get_historical_ohlcv,
    get_trading_pairs,
    get_watched_timeframes,
    get_base_currency,
    get_fees,
    get_max_handled_pair_with_time_frame,
    get_currently_handled_pair_with_time_frame,
    get_required_historical_candles_count,
    is_overloaded,
    cancel_ccxt_throttle_task,
    stop_exchange,
)
from octobot_trading.api.modes import (
    get_trading_modes,
    get_trading_mode_writers,
    get_trading_mode_symbol,
    get_trading_mode_current_state,
    get_activated_trading_mode,
    create_trading_modes,
    create_trading_mode,
)
from octobot_trading.api.trader import (
    get_trader,
    has_trader,
    is_trader_enabled_in_config_from_exchange_manager,
    is_trader_existing_and_enabled,
    is_trader_enabled,
    is_trader_enabled_in_config,
    is_trader_simulator_enabled_in_config,
    set_trading_enabled,
    is_trader_simulated,
    get_trader_risk,
    set_trader_risk,
    sell_all_everything_for_reference_market,
    sell_currency_for_reference_market,
)
from octobot_trading.api.portfolio import (
    get_portfolio,
    get_portfolio_historical_values,
    reset_portfolio_historical_values,
    get_portfolio_currency,
    get_origin_portfolio,
    refresh_real_trader_portfolio,
    format_portfolio,
    get_portfolio_amounts,
)
from octobot_trading.api.profitability import (
    get_profitability_stats,
    get_origin_portfolio_value,
    get_current_portfolio_value,
    get_current_holdings_values,
    get_current_crypto_currency_value,
    get_reference_market,
    get_initializing_currencies_prices,
)
from octobot_trading.api.orders import (
    get_open_orders,
    get_order_exchange_name,
    order_to_dict,
    parse_order_type,
    parse_order_status,
    get_order_profitability,
    create_order,
    cancel_all_open_orders,
    cancel_all_open_orders_with_currency,
    cancel_order_with_id,
    LOGGER,
)
from octobot_trading.api.positions import (
    get_positions,
)

__all__ = [
    "get_symbol_data",
    "get_symbol_candles_manager",
    "get_symbol_historical_candles",
    "are_symbol_candles_initialized",
    "get_candle_as_list",
    "has_symbol_klines",
    "get_symbol_klines",
    "get_symbol_candles_count",
    "get_symbol_close_candles",
    "get_symbol_open_candles",
    "get_symbol_high_candles",
    "get_symbol_low_candles",
    "get_symbol_volume_candles",
    "get_symbol_time_candles",
    "create_new_candles_manager",
    "force_set_mark_price",
    "is_mark_price_initialized",
    "get_trade_history",
    "get_total_paid_trading_fees",
    "get_trade_exchange_name",
    "parse_trade_type",
    "trade_to_dict",
    "get_win_rate",
    "subscribe_to_ohlcv_channel",
    "subscribe_to_trades_channel",
    "subscribe_to_order_channel",
    "create_exchange_builder",
    "get_exchange_configurations_from_exchange_name",
    "get_exchange_manager_from_exchange_name_and_id",
    "get_exchange_available_time_frames",
    "get_exchange_available_required_time_frames",
    "get_exchange_configuration_from_exchange_id",
    "get_exchange_manager_from_exchange_id",
    "get_exchange_managers_from_exchange_ids",
    "get_trading_exchanges",
    "is_exchange_trading",
    "get_exchange_manager_id",
    "get_exchange_manager_is_sandboxed",
    "get_exchange_current_time",
    "get_exchange_allowed_time_lag",
    "get_exchange_id_from_matrix_id",
    "get_matrix_id_from_exchange_id",
    "get_all_exchange_ids_from_matrix_id",
    "get_exchange_configuration_from_exchange",
    "get_all_exchange_ids_with_same_matrix_id",
    "get_exchange_names",
    "get_exchange_ids",
    "get_exchange_name",
    "has_only_ohlcv",
    "get_is_backtesting",
    "get_backtesting_data_files",
    "get_backtesting_data_file",
    "get_has_websocket",
    "supports_websockets",
    "is_compatible_account",
    "is_sponsoring",
    "is_valid_account",
    "get_historical_ohlcv",
    "get_trading_pairs",
    "get_watched_timeframes",
    "get_base_currency",
    "get_fees",
    "get_max_handled_pair_with_time_frame",
    "get_currently_handled_pair_with_time_frame",
    "get_required_historical_candles_count",
    "is_overloaded",
    "cancel_ccxt_throttle_task",
    "stop_exchange",
    "get_trading_modes",
    "get_trading_mode_writers",
    "get_trading_mode_symbol",
    "get_trading_mode_current_state",
    "get_activated_trading_mode",
    "create_trading_modes",
    "create_trading_mode",
    "get_trader",
    "has_trader",
    "is_trader_enabled_in_config_from_exchange_manager",
    "is_trader_existing_and_enabled",
    "is_trader_enabled",
    "is_trader_enabled_in_config",
    "is_trader_simulator_enabled_in_config",
    "set_trading_enabled",
    "is_trader_simulated",
    "get_trader_risk",
    "set_trader_risk",
    "sell_all_everything_for_reference_market",
    "sell_currency_for_reference_market",
    "get_portfolio",
    "get_portfolio_historical_values",
    "reset_portfolio_historical_values",
    "get_portfolio_currency",
    "get_origin_portfolio",
    "refresh_real_trader_portfolio",
    "get_portfolio_amounts",
    "get_origin_portfolio_value",
    "get_profitability_stats",
    "format_portfolio",
    "get_current_portfolio_value",
    "get_current_holdings_values",
    "get_current_crypto_currency_value",
    "get_reference_market",
    "get_initializing_currencies_prices",
    "get_open_orders",
    "get_order_exchange_name",
    "order_to_dict",
    "parse_order_type",
    "parse_order_status",
    "get_order_profitability",
    "create_order",
    "cancel_all_open_orders",
    "cancel_all_open_orders_with_currency",
    "cancel_order_with_id",
    "get_positions",
]
