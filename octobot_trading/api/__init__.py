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
from octobot_trading.api import contracts
from octobot_trading.api import storage

from octobot_trading.api.symbol_data import (
    get_symbol_data,
    get_symbol_candles_manager,
    get_symbol_historical_candles,
    create_preloaded_candles_manager,
    are_symbol_candles_initialized,
    get_candles_as_list,
    get_candle_as_list,
    has_symbol_klines,
    get_symbol_klines,
    get_symbol_candles_count,
    get_symbol_close_candles,
    get_symbol_open_candles,
    get_symbol_high_candles,
    get_symbol_low_candles,
    get_symbol_volume_candles,
    get_daily_base_and_quote_volume,
    get_daily_base_and_quote_volume_from_ticker,
    compute_base_and_quote_volume,
    get_symbol_time_candles,
    create_new_candles_manager,
    force_set_mark_price,
    is_mark_price_initialized,
    get_config_symbols,
)
from octobot_trading.api.trades import (
    get_trade_history,
    get_completed_pnl_history,
    get_trade_pnl,
    is_executed_trade,
    is_trade_after_or_at,
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
    get_ccxt_exchange_available_time_frames,
    get_exchange_available_required_time_frames,
    get_exchange_configuration_from_exchange_id,
    get_exchange_manager_from_exchange_id,
    get_exchange_managers_from_exchange_ids,
    get_trading_exchanges,
    is_exchange_trading,
    get_exchange_manager_id,
    get_exchange_manager_is_sandboxed,
    get_exchange_current_time,
    get_exchange_backtesting_time_window,
    get_exchange_allowed_time_lag,
    get_exchange_id_from_matrix_id,
    get_matrix_id_from_exchange_id,
    get_all_exchange_ids_from_matrix_id,
    get_exchange_configuration_from_exchange,
    get_all_exchange_ids_with_same_matrix_id,
    get_exchange_names,
    get_exchange_ids,
    get_exchange_name,
    get_exchange_type,
    has_only_ohlcv,
    get_is_backtesting,
    get_backtesting_data_files,
    get_backtesting_data_file,
    get_has_websocket,
    get_has_reached_websocket_limit,
    supports_websockets,
    is_compatible_account,
    get_new_ccxt_client,
    get_default_exchange_type,
    is_sponsoring,
    is_broker_enabled,
    get_historical_ohlcv,
    get_bot_id,
    get_supported_exchange_types,
    get_trading_pairs,
    get_all_exchange_symbols,
    get_all_exchange_time_frames,
    get_trading_symbols,
    get_trading_timeframes,
    get_watched_timeframes,
    get_relevant_time_frames,
    get_base_currency,
    get_fees,
    get_max_handled_pair_with_time_frame,
    get_currently_handled_pair_with_time_frame,
    get_required_historical_candles_count,
    is_overloaded,
    store_history_in_run_storage,
    get_enabled_exchanges_names,
    get_auto_filled_exchange_names,
    supports_custom_limit_order_book_fetch,
    get_exchange_details,
    cancel_ccxt_throttle_task,
    stop_exchange,
)
from octobot_trading.api.modes import (
    get_trading_modes,
    get_trading_mode_symbol,
    is_trading_mode_symbol_wildcard,
    get_trading_mode_followed_strategy_signals_identifier,
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
    get_current_bot_live_id,
)
from octobot_trading.api.portfolio import (
    get_portfolio,
    get_portfolio_historical_values,
    get_portfolio_reference_market,
    get_portfolio_currency,
    get_origin_portfolio,
    set_simulated_portfolio_initial_config,
    refresh_real_trader_portfolio,
    format_portfolio,
    parse_decimal_portfolio,
    get_draw_down,
    get_coefficient_of_determination,
    get_usd_like_symbol_from_symbols,
    get_usd_like_symbols_from_symbols,
    can_convert_symbol_to_usd_like,
    is_usd_like_coin,
    resolve_sub_portfolios,
    get_portfolio_filled_orders_deltas,
    get_global_portfolio_currencies_values,
)
from octobot_trading.api.profitability import (
    get_profitability_stats,
    get_origin_portfolio_value,
    get_current_portfolio_value,
    get_currency_ref_market_value,
    get_current_holdings_values,
    get_current_crypto_currency_value,
    get_reference_market,
    get_initializing_currencies_prices,
)
from octobot_trading.api.orders import (
    get_open_orders,
    get_pending_creation_orders,
    get_order_exchange_name,
    order_to_dict,
    parse_order_type,
    parse_order_status,
    is_order_pending,
    get_order_profitability,
    get_minimal_order_cost,
    get_order_trailing_profile_dict,
    create_order,
    cancel_all_open_orders,
    cancel_all_open_orders_with_currency,
    cancel_order_with_id,
    LOGGER,
)
from octobot_trading.api.positions import (
    get_positions,
    close_position,
    set_is_exclusively_using_exchange_position_details,
    update_position_mark_price,
)
from octobot_trading.api.contracts import (
    is_inverse_future_contract,
    is_perpetual_future_contract,
    get_pair_contracts,
    is_handled_contract,
    ensure_supported_contract_configuration,
    has_pair_future_contract,
    update_pair_contract,
    load_pair_contract,
    create_default_future_contract,
)
from octobot_trading.api.storage import (
    clear_trades_storage_history,
    clear_candles_storage_history,
    clear_database_storage_history,
    clear_transactions_storage_history,
    clear_portfolio_storage_history,
    clear_orders_storage_history,
    get_account_type,
    get_account_type_from_run_metadata,
    get_account_type_from_exchange_manager,
)

__all__ = [
    "get_symbol_data",
    "get_symbol_candles_manager",
    "get_symbol_historical_candles",
    "create_preloaded_candles_manager",
    "are_symbol_candles_initialized",
    "get_candles_as_list",
    "get_candle_as_list",
    "has_symbol_klines",
    "get_symbol_klines",
    "get_symbol_candles_count",
    "get_symbol_close_candles",
    "get_symbol_open_candles",
    "get_symbol_high_candles",
    "get_symbol_low_candles",
    "get_symbol_volume_candles",
    "get_daily_base_and_quote_volume",
    "get_daily_base_and_quote_volume_from_ticker",
    "compute_base_and_quote_volume",
    "get_symbol_time_candles",
    "create_new_candles_manager",
    "force_set_mark_price",
    "is_mark_price_initialized",
    "get_config_symbols",
    "get_trade_history",
    "get_completed_pnl_history",
    "get_trade_pnl",
    "is_executed_trade",
    "is_trade_after_or_at",
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
    "get_ccxt_exchange_available_time_frames",
    "get_exchange_available_required_time_frames",
    "get_exchange_configuration_from_exchange_id",
    "get_exchange_manager_from_exchange_id",
    "get_exchange_managers_from_exchange_ids",
    "get_trading_exchanges",
    "is_exchange_trading",
    "get_exchange_manager_id",
    "get_exchange_manager_is_sandboxed",
    "get_exchange_current_time",
    "get_exchange_backtesting_time_window",
    "get_exchange_allowed_time_lag",
    "get_exchange_id_from_matrix_id",
    "get_matrix_id_from_exchange_id",
    "get_all_exchange_ids_from_matrix_id",
    "get_exchange_configuration_from_exchange",
    "get_all_exchange_ids_with_same_matrix_id",
    "get_exchange_names",
    "get_exchange_ids",
    "get_exchange_name",
    "get_exchange_type",
    "has_only_ohlcv",
    "get_is_backtesting",
    "get_backtesting_data_files",
    "get_backtesting_data_file",
    "get_has_websocket",
    "get_has_reached_websocket_limit",
    "supports_websockets",
    "is_compatible_account",
    "get_new_ccxt_client",
    "get_default_exchange_type",
    "is_sponsoring",
    "is_broker_enabled",
    "get_historical_ohlcv",
    "get_bot_id",
    "get_supported_exchange_types",
    "get_trading_pairs",
    "get_all_exchange_symbols",
    "get_all_exchange_time_frames",
    "get_trading_symbols",
    "get_trading_timeframes",
    "get_watched_timeframes",
    "get_relevant_time_frames",
    "get_base_currency",
    "get_fees",
    "get_max_handled_pair_with_time_frame",
    "get_currently_handled_pair_with_time_frame",
    "get_required_historical_candles_count",
    "is_overloaded",
    "store_history_in_run_storage",
    "get_enabled_exchanges_names",
    "get_auto_filled_exchange_names",
    "supports_custom_limit_order_book_fetch",
    "get_exchange_details",
    "cancel_ccxt_throttle_task",
    "stop_exchange",
    "get_trading_modes",
    "get_trading_mode_symbol",
    "is_trading_mode_symbol_wildcard",
    "get_trading_mode_followed_strategy_signals_identifier",
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
    "get_current_bot_live_id",
    "get_portfolio",
    "get_portfolio_historical_values",
    "get_portfolio_reference_market",
    "get_portfolio_currency",
    "get_origin_portfolio",
    "set_simulated_portfolio_initial_config",
    "refresh_real_trader_portfolio",
    "get_draw_down",
    "get_coefficient_of_determination",
    "get_usd_like_symbol_from_symbols",
    "get_usd_like_symbols_from_symbols",
    "can_convert_symbol_to_usd_like",
    "is_usd_like_coin",
    "resolve_sub_portfolios",
    "get_portfolio_filled_orders_deltas",
    "get_global_portfolio_currencies_values",
    "get_origin_portfolio_value",
    "get_profitability_stats",
    "format_portfolio",
    "parse_decimal_portfolio",
    "get_current_portfolio_value",
    "get_currency_ref_market_value",
    "get_current_holdings_values",
    "get_current_crypto_currency_value",
    "get_reference_market",
    "get_initializing_currencies_prices",
    "get_open_orders",
    "get_pending_creation_orders",
    "get_order_exchange_name",
    "order_to_dict",
    "parse_order_type",
    "parse_order_status",
    "is_order_pending",
    "get_order_profitability",
    "get_minimal_order_cost",
    "get_order_trailing_profile_dict",
    "create_order",
    "cancel_all_open_orders",
    "cancel_all_open_orders_with_currency",
    "cancel_order_with_id",
    "get_positions",
    "close_position",
    "is_inverse_future_contract",
    "is_perpetual_future_contract",
    "get_pair_contracts",
    "is_handled_contract",
    "ensure_supported_contract_configuration",
    "has_pair_future_contract",
    "update_pair_contract",
    "load_pair_contract",
    "create_default_future_contract",
    "set_is_exclusively_using_exchange_position_details",
    "update_position_mark_price",
    "clear_trades_storage_history",
    "clear_candles_storage_history",
    "clear_database_storage_history",
    "get_account_type",
    "get_account_type_from_run_metadata",
    "get_account_type_from_exchange_manager",
    "clear_transactions_storage_history",
    "clear_portfolio_storage_history",
    "clear_orders_storage_history",
]
