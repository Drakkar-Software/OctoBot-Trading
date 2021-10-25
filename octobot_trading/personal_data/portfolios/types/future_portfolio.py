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
import octobot_trading.personal_data.portfolios.assets.future_asset as future_asset
import octobot_trading.personal_data.portfolios.portfolio as portfolio_class
import octobot_trading.constants as constants


class FuturePortfolio(portfolio_class.Portfolio):
    def create_currency_asset(self, currency, available=constants.ZERO, total=constants.ZERO):
        return future_asset.FutureAsset(name=currency, available=available, total=total)

    def update_portfolio_data_from_order(self, order):
        """
        Call update_portfolio_data for order currency and market
        :param order: the order that updated the portfolio
        """
        self._update_portfolio_from_future_order(order,
                                                 order_quantity=order.filled_quantity,
                                                 order_price=order.filled_price,
                                                 subtract_fees=True,
                                                 inverse_calculation=False)

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
                                                 inverse_calculation=not increase_quantity)

    def _update_portfolio_from_future_order(self, order,
                                            order_quantity,
                                            order_price,
                                            subtract_fees=False,
                                            inverse_calculation=False):
        """
        Update future portfolio from an order
        :param order: the order
        :param order_quantity: the order quantity to use for calculation
        :param order_price: the order price to use for calculation
        :param subtract_fees: when True, subtract fees to order quantity
        :param inverse_calculation: when True, inverse calculation (for example when a cancel occurred)
        """
        pair_future_contract = order.exchange_manager.exchange.get_pair_future_contract(order.symbol)

        # calculates the real order quantity depending on the current contract leverage
        real_order_quantity = ((order_quantity - (order.get_total_fees(order.currency) if subtract_fees else constants.ZERO))
                               / pair_future_contract.current_leverage)

        # When inverse contract, decrease a currency market equivalent quantity from currency balance
        if pair_future_contract.is_inverse_contract():
            # decrease currency market equivalent quantity from currency available balance
            self._update_portfolio_data(currency, available_value=(
                    -(real_order_quantity / order_price) * (-constants.ONE if inverse_calculation else constants.ONE)))

        # When non-inverse contract, decrease directly market quantity
        else:
            # decrease market quantity from market available balance
            self._update_portfolio_data(market, available_value=(
                    -real_order_quantity * (-constants.ONE if inverse_calculation else constants.ONE)))

    def update_portfolio_from_liquidated_position(self, position):
        """
        :param position: the liquidated position
        """
        new_quantity = -position.quantity
        self._update_portfolio_data(position.currency
                                    if position.symbol_contract.is_inverse_contract() else position.market,
                                    -position.quantity
                                    if position.is_long() else position.quantity,
                                    total=True,
                                    available=True)
