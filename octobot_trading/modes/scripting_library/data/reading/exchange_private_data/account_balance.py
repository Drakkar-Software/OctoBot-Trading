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

import octobot_commons.constants as commons_constants
import octobot_trading.constants as trading_constants
import octobot_trading.personal_data as trading_personal_data


async def total_account_balance(context=None):
    return context.exchange_manager.exchange_personal_data.\
        portfolio_manager.portfolio_value_holder.portfolio_current_value


async def available_account_balance(context=None, side="buy"):
    trade_data = await trading_personal_data.get_pre_order_data(context.trader.exchange_manager,
                                                                symbol=context.symbol,
                                                                timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT)
    current_symbol_holding, current_market_holding, market_quantity, current_price, symbol_market = trade_data

    if side == "buy":
        return current_market_holding / current_price
    else:
        return current_symbol_holding

    # todo handle reference market change
    # todo handle futures and margin
    #  for futures its (balance - frozen balance) * leverage
    #  _
    #  for live
    #  futures available blance based on exchange values
