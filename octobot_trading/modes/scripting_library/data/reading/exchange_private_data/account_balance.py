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
import octobot_trading.enums as trading_enums
import octobot_trading.personal_data as trading_personal_data


async def total_account_balance(context):
    current_price = \
        await trading_personal_data.get_up_to_date_price(context.exchange_manager,
                                                         symbol=context.symbol,
                                                         timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT)
    return context.exchange_manager.exchange_personal_data.\
        portfolio_manager.portfolio_value_holder.portfolio_current_value / current_price


async def available_account_balance(context, side=trading_enums.TradeOrderSide.BUY.value, use_total_holding=False):
    portfolio_type = commons_constants.PORTFOLIO_TOTAL if use_total_holding else commons_constants.PORTFOLIO_AVAILABLE
    current_symbol_holding, current_market_holding, market_quantity, current_price, symbol_market = \
        await trading_personal_data.get_pre_order_data(context.exchange_manager,
                                                       symbol=context.symbol,
                                                       timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT,
                                                       portfolio_type=portfolio_type)

    return market_quantity if side == trading_enums.TradeOrderSide.BUY.value else current_symbol_holding

    # todo handle reference market change
    # todo handle futures and margin
    #  for futures its (balance - frozen balance) * leverage
    #  _
    #  for live
    #  futures available balance based on exchange values


async def adapt_amount_to_holdings(context, amount, side, use_total_holding):
    available_acc_bal = await available_account_balance(context, side, use_total_holding=use_total_holding)
    if available_acc_bal > amount:
        return amount
    else:
        return available_acc_bal
