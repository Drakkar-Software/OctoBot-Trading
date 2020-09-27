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

from octobot_trading.api import channels
from octobot_trading.api import exchange
from octobot_trading.api import modes
from octobot_trading.api import orders
from octobot_trading.api import portfolio
from octobot_trading.api import profitability
from octobot_trading.api import symbol_data
from octobot_trading.api import trader
from octobot_trading.api import trades

from octobot_trading.api.channels import (subscribe_to_ohlcv_channel,
                                          subscribe_to_trades_channel,
                                          subscribe_to_order_channel, )
from octobot_trading.api.exchange import (cancel_ccxt_throttle_task,
                                          create_exchange_builder,
                                          get_all_exchange_ids_from_matrix_id,
                                          get_all_exchange_ids_with_same_matrix_id,
                                          get_base_currency,
                                          get_exchange_allowed_time_lag,
                                          get_exchange_configuration_from_exchange,
                                          get_exchange_configuration_from_exchange_id,
                                          get_exchange_configurations_from_exchange_name,
                                          get_exchange_current_time,
                                          get_exchange_id_from_matrix_id,
                                          get_exchange_ids,
                                          get_exchange_manager_from_exchange_id,
                                          get_exchange_manager_from_exchange_name_and_id,
                                          get_exchange_manager_id,
                                          get_exchange_managers_from_exchange_ids,
                                          get_exchange_name,
                                          get_exchange_names,
                                          get_exchange_time_frames_without_real_time,
                                          get_fees, get_is_backtesting,
                                          get_matrix_id_from_exchange_id,
                                          get_trading_exchanges,
                                          get_trading_pairs,
                                          get_watched_timeframes,
                                          has_only_ohlcv, is_exchange_trading, )
from octobot_trading.api.modes import (get_activated_trading_mode,
                                       get_trading_mode_current_state,
                                       get_trading_mode_symbol,
                                       get_trading_modes,
                                       create_trading_modes, )
from octobot_trading.api.orders import (get_open_orders,
                                        get_order_exchange_name,
                                        get_order_profitability, order_to_dict,
                                        parse_order_status, parse_order_type, )
from octobot_trading.api.portfolio import (get_origin_portfolio, get_portfolio,
                                           get_portfolio_currency, )
from octobot_trading.api.profitability import (get_current_holdings_values,
                                               get_current_portfolio_value,
                                               get_initializing_currencies_prices,
                                               get_origin_portfolio_value,
                                               get_profitability_stats,
                                               get_reference_market, )
from octobot_trading.api.symbol_data import (create_new_candles_manager,
                                             force_set_mark_price,
                                             get_candle_as_list,
                                             get_symbol_candles_manager,
                                             get_symbol_close_candles,
                                             get_symbol_data,
                                             get_symbol_high_candles,
                                             get_symbol_historical_candles,
                                             get_symbol_klines,
                                             get_symbol_low_candles,
                                             get_symbol_open_candles,
                                             get_symbol_time_candles,
                                             get_symbol_volume_candles,
                                             has_symbol_klines,
                                             is_mark_price_initialized, )
from octobot_trading.api.trader import (get_trader_risk,
                                        is_trader_enabled,
                                        is_trader_enabled_in_config,
                                        is_trader_enabled_in_config_from_exchange_manager,
                                        is_trader_simulated,
                                        is_trader_simulator_enabled_in_config,
                                        set_trader_risk, set_trading_enabled, )
from octobot_trading.api.trades import (get_total_paid_trading_fees,
                                        get_trade_exchange_name,
                                        get_trade_history, parse_trade_type,
                                        trade_to_dict, )

LOGGER_TAG = "TradingApi"

__all__ = ['LOGGER_TAG', 'cancel_ccxt_throttle_task',
           'channels', 'create_exchange_builder', 'create_new_candles_manager',
           'exchange', 'force_set_mark_price', 'get_activated_trading_mode',
           'get_all_exchange_ids_from_matrix_id',
           'get_all_exchange_ids_with_same_matrix_id', 'get_base_currency',
           'get_candle_as_list', 'get_current_holdings_values',
           'get_current_portfolio_value', 'get_exchange_allowed_time_lag',
           'get_exchange_configuration_from_exchange',
           'get_exchange_configuration_from_exchange_id',
           'get_exchange_configurations_from_exchange_name',
           'get_exchange_current_time', 'get_exchange_id_from_matrix_id',
           'get_exchange_ids', 'get_exchange_manager_from_exchange_id',
           'get_exchange_manager_from_exchange_name_and_id',
           'get_exchange_manager_id',
           'get_exchange_managers_from_exchange_ids', 'get_exchange_name',
           'get_exchange_names', 'get_exchange_time_frames_without_real_time',
           'get_fees', 'get_initializing_currencies_prices',
           'get_is_backtesting', 'get_matrix_id_from_exchange_id',
           'get_open_orders', 'get_order_exchange_name',
           'get_order_profitability', 'get_origin_portfolio',
           'get_origin_portfolio_value', 'get_portfolio',
           'get_portfolio_currency', 'get_profitability_stats',
           'get_reference_market', 'get_symbol_candles_manager',
           'get_symbol_close_candles', 'get_symbol_data',
           'get_symbol_high_candles', 'get_symbol_historical_candles',
           'get_symbol_klines', 'get_symbol_low_candles',
           'get_symbol_open_candles', 'get_symbol_time_candles',
           'get_symbol_volume_candles', 'get_total_paid_trading_fees',
           'get_trade_exchange_name', 'get_trade_history', 'get_trader_risk',
           'get_trading_exchanges', 'get_trading_mode_current_state',
           'get_trading_mode_symbol', 'get_trading_modes', 'get_trading_pairs',
           'get_watched_timeframes', 'has_only_ohlcv', 'has_symbol_klines',
           'is_exchange_trading', 'is_mark_price_initialized', 'is_trader_enabled',
           'is_trader_enabled_in_config',
           'is_trader_enabled_in_config_from_exchange_manager',
           'is_trader_simulated', 'is_trader_simulator_enabled_in_config',
           'modes', 'order_to_dict', 'orders', 'parse_order_status',
           'parse_order_type', 'parse_trade_type', 'portfolio',
           'profitability', 'set_trader_risk', 'set_trading_enabled',
           'symbol_data', 'trade_to_dict', 'trader', 'trades',
           'subscribe_to_ohlcv_channel', 'subscribe_to_trades_channel', 'subscribe_to_order_channel']
