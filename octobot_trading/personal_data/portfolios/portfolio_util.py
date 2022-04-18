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
import octobot_trading.personal_data.portfolios.asset as asset


def parse_decimal_portfolio(portfolio):
    decimal_portfolio = {}
    for symbol, symbol_balance in portfolio.items():
        if isinstance(symbol_balance, dict):
            decimal_portfolio[symbol] = {}
            portfolio_to_fill = decimal_portfolio[symbol]
            for balance_type, balance_val in symbol_balance.items():
                if isinstance(balance_val, (int, float, decimal.Decimal)):
                    portfolio_to_fill[balance_type] = decimal.Decimal(str(balance_val))
    return decimal_portfolio


def parse_decimal_config_portfolio(portfolio):
    return {
        symbol: decimal.Decimal(str(symbol_balance))
        for symbol, symbol_balance in portfolio.items()
    }


def portfolio_to_float(portfolio):
    float_portfolio = {}
    for symbol, symbol_balance in portfolio.items():
        if isinstance(symbol_balance, asset.Asset):
            float_portfolio[symbol] = {
                "available": float(symbol_balance.available),
                "total": float(symbol_balance.total)
            }
    return float_portfolio


def get_draw_down(exchange_manager):
    """
    Draw down is the lowest portfolio value in % ever reached during a run
    :param exchange_manager:
    :return:
    """
    draw_down = 0
    if exchange_manager.is_future:
        origin_portfolio = portfolio_to_float(
            exchange_manager.exchange_personal_data.portfolio_manager.portfolio_value_holder.origin_portfolio.portfolio
        )
        portfolio_history = [
            origin_portfolio[exchange_manager.exchange_personal_data.portfolio_manager.reference_market]["total"]]
        for transaction in exchange_manager.exchange_personal_data.transactions_manager.transactions.values():
            current_pnl = float(transaction.quantity if hasattr(transaction, "quantity") else transaction.realised_pnl)
            portfolio_history.append(portfolio_history[-1] + current_pnl)

            current_draw_down = 100 - (portfolio_history[-1] / (max(portfolio_history) / 100))

            draw_down = current_draw_down if current_draw_down > draw_down else draw_down
    return draw_down
