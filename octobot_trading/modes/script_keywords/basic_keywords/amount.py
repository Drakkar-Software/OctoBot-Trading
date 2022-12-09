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

import octobot_trading.modes.script_keywords.dsl as dsl
import octobot_trading.modes.script_keywords.basic_keywords.account_balance as account_balance
import octobot_trading.errors as trading_errors
import octobot_trading.enums as trading_enums


async def get_amount_from_input_amount(
    context=None,
    input_amount=None,
    side=trading_enums.TradeOrderSide.BUY.value,
    reduce_only=True,
    is_stop_order=False,
    use_total_holding=False,
    target_price=None,
):
    amount_type, amount_value = dsl.parse_quantity(input_amount)

    if amount_type is dsl.QuantityType.UNKNOWN or amount_value <= 0:
        raise trading_errors.InvalidArgumentError("amount cant be zero or negative")

    if amount_type is dsl.QuantityType.DELTA:
        # nothing to do
        pass
    elif amount_type is dsl.QuantityType.PERCENT:
        amount_value = await account_balance.total_account_balance(context) * amount_value / 100
    elif amount_type is dsl.QuantityType.AVAILABLE_PERCENT:
        amount_value = await account_balance.available_account_balance(context, side, reduce_only=reduce_only) \
                       * amount_value / 100
    elif amount_type is dsl.QuantityType.POSITION_PERCENT:
        raise NotImplementedError(amount_type)
    else:
        raise trading_errors.InvalidArgumentError("make sure to use a supported syntax for amount")
    return await account_balance.adapt_amount_to_holdings(context, amount_value, side,
                                                          use_total_holding, reduce_only, is_stop_order,
                                                          target_price=target_price)
