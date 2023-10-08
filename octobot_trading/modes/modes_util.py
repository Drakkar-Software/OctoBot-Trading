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
import octobot_commons.databases as databases
import octobot_commons.constants as common_constants
import octobot_commons.symbols as symbol_util

import octobot_tentacles_manager.api as tentacles_manager_api
import octobot_trading.constants as constants
import octobot_trading.storage as storage
import octobot_trading.enums as trading_enums
import octobot_trading.modes.script_keywords.basic_keywords as basic_keywords
import octobot_trading.exchanges.util.exchange_util as exchange_util
import octobot_trading.personal_data as trading_personal_data


def get_required_candles_count(trading_mode_class, tentacles_setup_config):
    return tentacles_manager_api.get_tentacle_config(tentacles_setup_config, trading_mode_class).get(
        constants.CONFIG_CANDLES_HISTORY_SIZE_KEY,
        common_constants.DEFAULT_IGNORED_VALUE
    )


async def clear_simulated_orders_cache(trading_mode):
    await basic_keywords.clear_orders_cache(
        databases.RunDatabasesProvider.instance().get_orders_db(
            trading_mode.bot_id,
            storage.get_account_type_suffix_from_exchange_manager(trading_mode.exchange_manager),
            trading_mode.exchange_manager.exchange_name
        )
    )


async def clear_plotting_cache(trading_mode):
    await basic_keywords.clear_symbol_plot_cache(
        databases.RunDatabasesProvider.instance().get_symbol_db(
            trading_mode.bot_id,
            trading_mode.exchange_manager.exchange_name, trading_mode.symbol
        )
    )


async def convert_to_target_asset(trading_mode, sellable_assets: list, target_asset: str):
    portfolio = trading_mode.exchange_manager.exchange_personal_data.portfolio_manager.portfolio
    async with portfolio.lock:
        for asset in sellable_assets:
            if asset in portfolio and portfolio[asset].available:
                symbol = symbol_util.merge_currencies(asset, target_asset)
                order_type = trading_enums.TraderOrderType.SELL_MARKET
                if symbol not in trading_mode.exchange_manager.client_symbols:
                    # try reversed
                    reversed_symbol = symbol_util.merge_currencies(target_asset, asset)
                    if reversed_symbol not in trading_mode.exchange_manager.client_symbols:
                        # can't convert asset into target_asset
                        trading_mode.logger.error(
                            f"Impossible to convert {asset} into {target_asset}: no {symbol} or "
                            f"{reversed_symbol} trading pair on {trading_mode.exchange_manager.exchange_name}"
                        )
                        continue
                    symbol = reversed_symbol
                    order_type = trading_enums.TraderOrderType.BUY_MARKET
                current_symbol_holding, current_market_holding, market_quantity, price, symbol_market = \
                    await trading_personal_data.get_pre_order_data(
                        trading_mode.exchange_manager, symbol=symbol,
                        timeout=constants.ORDER_DATA_FETCHING_TIMEOUT
                    )
                quantity = current_symbol_holding if order_type is trading_enums.TraderOrderType.SELL_MARKET \
                    else current_market_holding
                for order_quantity, order_price in \
                        trading_personal_data.decimal_check_and_adapt_order_details_if_necessary(
                            quantity,
                            price,
                            symbol_market
                        ):
                    order = trading_personal_data.create_order_instance(
                        trader=trading_mode.exchange_manager.trader,
                        order_type=order_type,
                        symbol=symbol,
                        current_price=price,
                        quantity=order_quantity,
                        price=price
                    )
                    await trading_mode.create_order(order)
