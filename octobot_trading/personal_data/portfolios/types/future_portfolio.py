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
import octobot_trading.constants as constants


class FuturePortfolio(portfolio_class.Portfolio):
    def update_portfolio_data_from_order(self, order, currency, market):
        """
        Call update_portfolio_data for order currency and market
        :param order: the order that updated the portfolio
        :param currency: the order currency
        :param market: the order market
        """
        self._update_portfolio_from_future_order(order,
                                                 order_quantity=order.filled_quantity,
                                                 order_price=order.filled_price,
                                                 subtract_fees=True,
                                                 inverse_calculation=False,
                                                 update_available=True,
                                                 update_total=False)

    def update_portfolio_available_from_order(self, order, increase_quantity=True):
        """
        Realise portfolio availability update
        :param order: the order that triggers the portfolio update
        :param increase_quantity: True when increasing quantity
        """
        self._update_portfolio_from_future_order(order,
                                                 order_quantity=order.origin_quantity,
                                                 order_price=order.origin_price,
                                                 subtract_fees=False,
                                                 inverse_calculation=not increase_quantity,
                                                 update_available=True,
                                                 update_total=False)

    def _update_portfolio_from_future_order(self, order,
                                            order_quantity,
                                            order_price,
                                            subtract_fees=False,
                                            inverse_calculation=False,
                                            update_available=False,
                                            update_total=False):
        """
        Update future portfolio from an order
        :param order: the order
        :param order_quantity: the order quantity to use for calculation
        :param order_price: the order price to use for calculation
        :param subtract_fees: when True, subtract fees to order quantity
        :param inverse_calculation: when True, inverse calculation (for example when a cancel occurred)
        :param update_available: when True, update the available quantity of the portfolio
        :param update_total: when True, update the total quantity of the portfolio
        """
        currency, market = order.get_currency_and_market()
        pair_future_contract = order.exchange_manager.exchange.get_pair_future_contract(order.symbol)

        # calculates the real order quantity depending on the current contract leverage
        real_order_quantity = ((order_quantity - (order.get_total_fees(currency) if subtract_fees else constants.ZERO))
                               / pair_future_contract.current_leverage)

        # When inverse contract, decrease a currency market equivalent quantity from currency balance
        if pair_future_contract.is_inverse_contract():
            # decrease currency market equivalent quantity from currency available balance
            self._update_portfolio_data(currency,
                                        -(real_order_quantity / order_price) * (-constants.ONE if inverse_calculation else constants.ONE),
                                        total=update_total,
                                        available=update_available)

        # When non-inverse contract, decrease directly market quantity
        else:
            # decrease market quantity from market available balance
            self._update_portfolio_data(market,
                                        -real_order_quantity * (-constants.ONE if inverse_calculation else constants.ONE),
                                        total=update_total,
                                        available=update_available)

    def log_portfolio_update_from_order(self, order, currency, market):
        """
        TODO
        :param order: the order to log
        :param currency: the order currency
        :param market: the order market
        """
        self.logger.debug(f"Portfolio updated from order "
                          f"| {currency} TODO "
                          f"| {market} TODO "
                          f"| {constants.CURRENT_PORTFOLIO_STRING} {self.portfolio}")
