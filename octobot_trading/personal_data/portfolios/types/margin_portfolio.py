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
import octobot_commons.constants as common_constants

import octobot_trading.constants as constants
import octobot_trading.personal_data.portfolios.portfolio as portfolio_class


class MarginPortfolio(portfolio_class.Portfolio):
    # parse the exchange balance
    def _parse_currency_balance(self, currency_balance):
        return self._create_currency_portfolio(
            available=currency_balance[constants.CONFIG_PORTFOLIO_FREE]
            if constants.CONFIG_PORTFOLIO_FREE in currency_balance else currency_balance[
                common_constants.PORTFOLIO_AVAILABLE],
            margin=currency_balance[constants.CONFIG_PORTFOLIO_MARGIN]
            if constants.CONFIG_PORTFOLIO_MARGIN in currency_balance else (
                currency_balance[common_constants.MARGIN_PORTFOLIO]
                if common_constants.MARGIN_PORTFOLIO in currency_balance else 0),
            total=currency_balance[constants.CONFIG_PORTFOLIO_TOTAL]
            if constants.CONFIG_PORTFOLIO_TOTAL in currency_balance else currency_balance[
                common_constants.PORTFOLIO_TOTAL])

    def _create_currency_portfolio(self, available, total, margin=0):
        return {
            common_constants.PORTFOLIO_AVAILABLE: available,
            common_constants.MARGIN_PORTFOLIO: margin,
            common_constants.PORTFOLIO_TOTAL: total
        }

    def _reset_currency_portfolio(self, currency):
        self._set_currency_portfolio(currency=currency, available=0, total=0, margin=0)

    def _set_currency_portfolio(self, currency, available, total, margin=0):
        self.portfolio[currency] = self._create_currency_portfolio(available=available, total=total, margin=margin)

    def _update_currency_portfolio(self, currency, available=0, total=0, margin=0):
        self.portfolio[currency][common_constants.PORTFOLIO_AVAILABLE] += \
            portfolio_class.ensure_portfolio_update_validness(
            currency, self.portfolio[currency][common_constants.PORTFOLIO_AVAILABLE], available
        )
        self.portfolio[currency][common_constants.MARGIN_PORTFOLIO] += \
            portfolio_class.ensure_portfolio_update_validness(
                currency, self.portfolio[currency][common_constants.MARGIN_PORTFOLIO], margin
            )
        self.portfolio[currency][common_constants.PORTFOLIO_TOTAL] += portfolio_class.ensure_portfolio_update_validness(
            currency, self.portfolio[currency][common_constants.PORTFOLIO_TOTAL], total
        )
