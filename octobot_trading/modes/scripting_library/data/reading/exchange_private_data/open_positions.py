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
import octobot_trading.personal_data as personal_data
import octobot_trading.constants as trading_constants


def open_position_size(
        context=None,
        side=None
):
    if context.exchange_manager.is_future:
        raise NotImplementedError("future is not implemented")
    currency = symbol_util.split_symbol(context.symbol)[0]
    return context.exchange_manager.exchange_personal_data.portfolio_manager.portfolio.get_currency_portfolio(
        currency,
        portfolio_type=commons_constants.PORTFOLIO_TOTAL
    )
    # todo handle reference market change
    # todo handle futures: its account balance from exchange
    # todo handle futures and return negative for shorts


async def average_open_pos_entry(
        context,
        side
):

    if context.exchange_manager.is_future:
        raise NotImplementedError("future is not implemented")
    # for spot just get the current currency value
    return await personal_data.get_up_to_date_price(context.exchange_manager, context.symbol,
                                                    timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT)


def is_position_open(
        context=None,
        side=None
):
    return open_position_size(context, side=side) != trading_constants.ZERO
