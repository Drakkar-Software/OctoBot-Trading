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

import octobot_trading.modes.scripting_library.dsl as dsl
import octobot_trading.errors as trading_errors
import octobot_trading.enums as trading_enums
import octobot_trading.modes.scripting_library.data.reading.exchange_private_data as exchange_private_data
import octobot_commons.constants as commons_constants


async def get_amount(
    context=None,
    input_amount=None,
    side=trading_enums.TradeOrderSide.BUY.value,
    use_total_holding=False
):
    amount_type, amount_value = dsl.parse_quantity(input_amount)

    if amount_type is dsl.QuantityType.UNKNOWN or amount_value <= 0:
        raise trading_errors.InvalidArgumentError("amount cant be zero or negative")

    if amount_type is dsl.QuantityType.DELTA:
        # nothing to do
        pass
    elif amount_type is dsl.QuantityType.PERCENT:
        amount_value = await exchange_private_data.total_account_balance(context) * amount_value / 100
    elif amount_type is dsl.QuantityType.AVAILABLE_PERCENT:
        amount_value = await exchange_private_data.available_account_balance(context, side) * amount_value / 100
    elif amount_type is dsl.QuantityType.POSITION_PERCENT:  # todo handle existing open short position
        amount_value = \
            exchange_private_data.open_position_size(context, side, amount_type=commons_constants.PORTFOLIO_AVAILABLE) \
            * amount_value / 100
    else:
        raise trading_errors.InvalidArgumentError("make sure to use a supported syntax for amount")
    return await exchange_private_data.adapt_amount_to_holdings(context, amount_value, side, use_total_holding)
