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
import octobot_trading.personal_data.portfolios.portfolio as portfolio_class


class FuturePortfolio(portfolio_class.Portfolio):
    def update_portfolio_available_from_order(self, order, increase_quantity=True):
        """
        Realise portfolio availability update
        TODO support leverage
        :param order: the order that triggers the portfolio update
        :param increase_quantity: True when increasing quantity
        """
        currency, market = order.get_currency_and_market()

        is_inverse_contract = True  # TODO

        # When inverse contract, decrease a currency market equivalent quantity from currency balance
        if is_inverse_contract:
            # decrease currency market equivalent quantity from currency available balance
            self._update_portfolio_data(currency, -(order.origin_quantity / order.origin_price), False, True)

        # When non-inverse contract, decrease directly market quantity
        else:
            # decrease market quantity from market available balance
            self._update_portfolio_data(market, -order.origin_quantity, False, True)
