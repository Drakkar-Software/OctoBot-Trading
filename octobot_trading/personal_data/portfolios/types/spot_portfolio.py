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
import octobot_trading.constants as constants
import octobot_trading.enums as enums
import octobot_trading.personal_data.portfolios.portfolio as portfolio_class


class SpotPortfolio(portfolio_class.Portfolio):
    def update_portfolio_data_from_order(self, order, currency, market):
        """
        Call update_portfolio_data for order currency and market
        :param order: the order that updated the portfolio
        :param currency: the order currency
        :param market: the order market
        """
        # update currency
        if order.side == enums.TradeOrderSide.BUY:
            new_quantity = order.filled_quantity - order.get_total_fees(currency)
            self._update_portfolio_data(currency, new_quantity, True, True)
        else:
            new_quantity = -order.filled_quantity
            self._update_portfolio_data(currency, new_quantity, True, False)

        # update market
        if order.side == enums.TradeOrderSide.BUY:
            new_quantity = -(order.filled_quantity * order.filled_price)
            self._update_portfolio_data(market, new_quantity, True, False)
        else:
            new_quantity = (order.filled_quantity * order.filled_price) - order.get_total_fees(market)
            self._update_portfolio_data(market, new_quantity, True, True)

    def update_portfolio_available_from_order(self, order, increase_quantity=True):
        """
        Realise portfolio availability update
        :param order: the order that triggers the portfolio update
        :param increase_quantity: True when increasing quantity
        """
        currency, market = order.get_currency_and_market()

        # when buy order
        if order.side == enums.TradeOrderSide.BUY:
            new_quantity = - order.origin_quantity * order.origin_price * (constants.ONE if increase_quantity else -constants.ONE)
            self._update_portfolio_data(market, new_quantity, False, True)

        # when sell order
        else:
            new_quantity = - order.origin_quantity * (constants.ONE if increase_quantity else -constants.ONE)
            self._update_portfolio_data(currency, new_quantity, False, True)

    def log_portfolio_update_from_order(self, order, currency, market):
        """
        Log a portfolio update from an order
        :param order: the order that updated the portfolio
        :param currency: the order currency
        :param market: the order market
        """
        if order.side == enums.TradeOrderSide.BUY:
            currency_portfolio_num = order.filled_quantity - order.get_total_fees(currency)
            market_portfolio_num = -order.filled_quantity * order.filled_price
        else:
            currency_portfolio_num = -order.filled_quantity
            market_portfolio_num = order.filled_quantity * order.filled_price - order.get_total_fees(market)

        self.logger.debug(f"Portfolio updated from order | {currency} {currency_portfolio_num} | {market} "
                          f"{market_portfolio_num} | {constants.CURRENT_PORTFOLIO_STRING} {self.portfolio}")
