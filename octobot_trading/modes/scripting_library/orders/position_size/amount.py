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
import octobot_trading.modes.scripting_library.data.reading.exchange_private_data as exchange_private_data


async def get_amount(
        context=None,
        input_amount=None,
        side="buy"
):
    amount_type, amount_value = dsl.parse_quantity(input_amount)

    if amount_type is dsl.QuantityType.UNKNOWN or amount_value <= 0:
        raise RuntimeError("amount cant be zero or negative")

    if amount_type is dsl.QuantityType.DELTA:
        # nothing to do
        pass
    elif amount_type is dsl.QuantityType.PERCENT:
        amount_value = await exchange_private_data.total_account_balance(context) * amount_value / 100
    elif amount_type is dsl.QuantityType.AVAILABLE_PERCENT:
        amount_value = await exchange_private_data.available_account_balance(context, side) * amount_value / 100
    elif amount_type is dsl.QuantityType.POSITION_PERCENT:
        amount_value = exchange_private_data.open_position_size(context, side) * amount_value / 100
    else:
        raise RuntimeError("make sure to use a supported syntax for amount")
    return await exchange_private_data.adapt_amount_to_holdings(context, amount_value, side)
