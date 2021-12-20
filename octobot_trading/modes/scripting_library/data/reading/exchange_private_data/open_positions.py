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
import octobot_trading.modes.scripting_library.data.reading.exchange_public_data as exchange_public_data
import octobot_trading.modes.scripting_library.orders.offsets.offset as offsets
import octobot_trading.modes.scripting_library.orders.position_size.amount as amounts


# returns negative values when in a short position
def open_position_size(
        context,
        side="both",
        symbol=None,
        amount_type=commons_constants.PORTFOLIO_TOTAL
):
    if context.exchange_manager.is_future:
        raise NotImplementedError("future is not implemented")
    symbol = symbol or context.symbol
    currency = symbol_util.split_symbol(symbol)[0]
    return context.exchange_manager.exchange_personal_data.portfolio_manager.portfolio.get_currency_portfolio(
        currency,
        portfolio_type=amount_type
    )
    # todo handle reference market change
    # todo handle futures: its account balance from exchange
    # todo handle futures and return negative for shorts


# todo handle hedge mode and futures
#  position is negative when in a short
async def position_size_less_than(
        context,
        amount,
        side="both",
        symbol=None
):
    if context.exchange_manager.is_future:
        raise NotImplementedError("future is not implemented")
    symbol = symbol or context.symbol
    currency = symbol_util.split_symbol(symbol)[0]
    return await amounts.get_amount(context, amount) < context.exchange_manager.exchange_personal_data.\
        portfolio_manager.portfolio.get_currency_portfolio(
        currency,
        portfolio_type=commons_constants.PORTFOLIO_TOTAL
    )


async def average_open_pos_entry(
        context,
        side="long"
):
    # todo for spot: collect data to get average entry and use input field for already existing funds
    if context.exchange_manager.is_future:
        raise NotImplementedError("future is not implemented")
    # for spot just get the current currency value
    return await personal_data.get_up_to_date_price(context.exchange_manager, context.symbol,
                                                    timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT)


def is_position_open(
        context,
        side=None
):
    if side is None:
        long_open = open_position_size(context, side="long") != trading_constants.ZERO
        short_open = open_position_size(context, side="short") != trading_constants.ZERO
        return True if long_open or short_open else False
    else:
        return open_position_size(context, side=side) != trading_constants.ZERO


def is_position_none(
        context,
        side=None
):
    if side is None:
        long_none = open_position_size(context, side="long") == trading_constants.ZERO
        short_none = open_position_size(context, side="short") == trading_constants.ZERO
        return short_none and long_none
    else:
        return open_position_size(context, side=side) == trading_constants.ZERO


def is_position_long(
        context,
):
    return open_position_size(context, side="long") != trading_constants.ZERO


def is_position_short(
        context,
):
    return open_position_size(context, side="short") != trading_constants.ZERO


# todo make sure min_distance_to_entry works with %
async def is_position_in_profit(
        context,
        side="long",
        min_distance_to_entry="0.1%"  # can be % or a price
):
    if side == "long":
        return await average_open_pos_entry(context, side) + \
               await offsets.get_offset(context, min_distance_to_entry + "e", side="buy") \
               < await exchange_public_data.current_live_price(context)

    elif side == "short":
        return await average_open_pos_entry(context, side) - \
               await offsets.get_offset(context, min_distance_to_entry + "e", side="sell") \
               > await exchange_public_data.current_live_price(
            context)  # todo add minus in front of min_distance_to_entry
    else:
        raise RuntimeError("is_position_in_profit: side needs to be short or long")


async def is_position_in_loss(
        context,
        side="long",
):
    if side == "long":
        return await average_open_pos_entry(context, side) > await exchange_public_data.current_live_price(context)

    elif side == "short":
        return await average_open_pos_entry(context, side) < await exchange_public_data.current_live_price(context)
    else:
        raise RuntimeError("is_position_in_loss: side needs to be short or long")
