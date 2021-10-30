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
