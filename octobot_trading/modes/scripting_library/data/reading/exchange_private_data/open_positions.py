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

import octobot_commons.symbol_util as symbol_util
import octobot_commons.constants as commons_constants


def open_position_size(
        context=None,
        side=None
):
    if context.exchange_manager.is_future:
        # TODO
        return
    currency = symbol_util.split_symbol(context.symbol)[0]
    return context.exchange_manager.exchange_personal_data.portfolio_manager.portfolio.get_currency_portfolio(
        currency,
        portfolio_type=commons_constants.PORTFOLIO_TOTAL
    )
    # todo handle reference market change
    # todo handle futures: its account balance from exchange
    # todo handle futures and return negative for shorts


def average_open_pos_entry(
        context,
        side
):

    if context.exchange_manager.is_future:
        # TODO
        return
    # for spot just get the current currency value
    currency = symbol_util.split_symbol(context.symbol)[0]
    return context.exchange_manager.exchange_personal_data.portfolio_manager. \
        portfolio_value_holder.current_crypto_currencies_values[currency]


async def is_position_open(
        context=None,
        side=None
):
    #TODO
    pass