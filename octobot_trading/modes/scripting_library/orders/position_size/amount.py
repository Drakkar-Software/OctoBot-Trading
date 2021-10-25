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

import decimal
import octobot_commons.symbol_util as symbol_util
import octobot_commons.constants as common_constants
import re


def amount(input_amount, side, current_symbol_holding, market_quantity):
    amount_type = re.sub(r"\d|\.", "", input_amount)
    amount_value = decimal.Decimal(input_amount.replace(amount_type, ""))
    if amount_value is None:
        raise RuntimeError("Provide at least side with amount or target_position.")
    if amount_type == "":
        return input_amount
    if amount_type == "%":
        if side == "sell":
            return current_symbol_holding * amount_value / 100
        return market_quantity * amount_value / 100
    if amount_type == "%a":
        # todo later: handle symbol etc
        currency, market = symbol_util.split_symbol(symbol)
        currency_to_use = currency if side == "sell" else market
        total_amount = trader.exchange_manager.exchange_personal_data.portfolio_manager.portfolio.get_currency_portfolio(
            currency_to_use,
            common_constants.PORTFOLIO_TOTAL
        )
        if side == "sell":
            return total_amount * amount / 100
        return total_amount / price * amount / 100

    if amount_type == "%p":
        current_position_size = None  # todo
        return input_amount * current_position_size / 100

    else:
        raise RuntimeError("make sure to use a supported syntax for amount")
