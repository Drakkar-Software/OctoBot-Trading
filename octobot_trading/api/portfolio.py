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

import octobot_trading.exchange_channel as exchange_channel
import octobot_trading.constants
import octobot_trading.personal_data as personal_data


def get_portfolio(exchange_manager, as_decimal=True) -> dict:
    return format_portfolio(
        exchange_manager.exchange_personal_data.portfolio_manager.portfolio.portfolio,
        as_decimal
    )


def get_portfolio_historical_values(exchange_manager, currency, time_frame, from_timestamp=None, to_timestamp=None) \
        -> dict:
    return exchange_manager.exchange_personal_data.portfolio_manager.get_portfolio_historical_values(
        currency, time_frame, from_timestamp, to_timestamp
    )


async def reset_portfolio_historical_values(exchange_manager):
    await exchange_manager.exchange_personal_data.portfolio_manager.historical_portfolio_value_manager.reset_history()


def get_portfolio_currency(exchange_manager, currency) -> personal_data.Asset:
    return exchange_manager.exchange_personal_data.portfolio_manager.portfolio.get_currency_portfolio(currency)


def get_origin_portfolio(exchange_manager, as_decimal=True) -> dict:
    return format_portfolio(
        exchange_manager.exchange_personal_data.portfolio_manager.portfolio_value_holder.origin_portfolio.portfolio,
        as_decimal
    )


def format_portfolio(portfolio, as_decimal) -> dict:
    if as_decimal:
        return portfolio
    return personal_data.portfolio_to_float(portfolio)


async def refresh_real_trader_portfolio(exchange_manager) -> bool:
    return await exchange_channel.get_chan(octobot_trading.constants.BALANCE_CHANNEL, exchange_manager.id). \
        get_internal_producer(). \
        refresh_real_trader_portfolio(True)


def get_draw_down(exchange_manager) -> decimal.Decimal:
    return personal_data.get_draw_down(exchange_manager)


async def get_coefficient_of_determination(exchange_manager, use_high_instead_of_end_balance=True):
    return await personal_data.get_coefficient_of_determination(exchange_manager,
                                                                use_high_instead_of_end_balance)
