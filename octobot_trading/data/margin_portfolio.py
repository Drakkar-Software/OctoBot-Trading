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
from octobot_commons.constants import PORTFOLIO_AVAILABLE, PORTFOLIO_TOTAL, MARGIN_PORTFOLIO
from octobot_trading.constants import CONFIG_PORTFOLIO_FREE, CONFIG_PORTFOLIO_TOTAL, CONFIG_PORTFOLIO_MARGIN
from octobot_trading.data.portfolio import Portfolio


class MarginPortfolio(Portfolio):
    async def update_portfolio_from_position(self, position):
        pass  # TODO

    # parse the exchange balance
    def _parse_currency_balance(self, currency_balance):
        return self._create_currency_portfolio(
            available=currency_balance[CONFIG_PORTFOLIO_FREE]
            if CONFIG_PORTFOLIO_FREE in currency_balance else currency_balance[PORTFOLIO_AVAILABLE],
            margin=currency_balance[CONFIG_PORTFOLIO_MARGIN]
            if CONFIG_PORTFOLIO_MARGIN in currency_balance else (currency_balance[MARGIN_PORTFOLIO]
                                                                 if MARGIN_PORTFOLIO in currency_balance else 0),
            total=currency_balance[CONFIG_PORTFOLIO_TOTAL]
            if CONFIG_PORTFOLIO_TOTAL in currency_balance else currency_balance[PORTFOLIO_TOTAL])

    def _create_currency_portfolio(self, available, total, margin=0):
        return {PORTFOLIO_AVAILABLE: available, MARGIN_PORTFOLIO: margin, PORTFOLIO_TOTAL: total}

    def _reset_currency_portfolio(self, currency):
        self._set_currency_portfolio(currency=currency, available=0, total=0, margin=0)

    def _set_currency_portfolio(self, currency, available, total, margin=0):
        self.portfolio[currency] = self._create_currency_portfolio(available=available, total=total, margin=margin)

    def _update_currency_portfolio(self, currency, available=0, total=0, margin=0):
        self.portfolio[currency][PORTFOLIO_AVAILABLE] += available
        self.portfolio[currency][MARGIN_PORTFOLIO] += margin
        self.portfolio[currency][PORTFOLIO_TOTAL] += total
