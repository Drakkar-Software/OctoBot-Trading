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


def get_profitability_stats(exchange_manager):
    port_profit = exchange_manager.exchange_personal_data.portfolio_manager.portfolio_profitability
    return port_profit.profitability, \
        port_profit.profitability_percent, \
        port_profit.profitability_diff, \
        port_profit.market_profitability_percent, \
        port_profit.initial_portfolio_current_profitability


def get_origin_portfolio_value(exchange_manager):
    return exchange_manager.exchange_personal_data.portfolio_manager.portfolio_profitability.portfolio_origin_value


def get_current_portfolio_value(exchange_manager):
    return exchange_manager.exchange_personal_data.portfolio_manager.portfolio_profitability.portfolio_current_value


def get_current_holdings_values(exchange_manager):
    return exchange_manager.exchange_personal_data.portfolio_manager.\
        portfolio_profitability.get_current_holdings_values()
