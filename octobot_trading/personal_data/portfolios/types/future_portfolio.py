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
        pair_future_contract = order.exchange_manager.exchange.get_pair_future_contract(order.symbol)
        try:
            real_filled_order_quantity = (order.origin_quantity - order.get_total_fees(order.currency)) / \
                                  pair_future_contract.current_leverage

            # When inverse contract, decrease a currency market equivalent quantity from currency balance
            if pair_future_contract.is_inverse_contract():
                total_update_quantity = real_filled_order_quantity / order.filled_price
                self._update_portfolio_data(order.currency,
                                            # restore available + total update
                                            available_value=decimal.Decimal(2) * total_update_quantity,
                                            total_value=total_update_quantity)

            # When non-inverse contract, decrease directly market quantity
            else:
                # decrease market quantity from market available balance
                total_update_quantity = real_filled_order_quantity * order.origin_price
                self._update_portfolio_data(order.market,
                                            # restore available + total update
                                            available_value=decimal.Decimal(2) * total_update_quantity,
                                            total_value=total_update_quantity)
        except (decimal.DivisionByZero, decimal.InvalidOperation) as e:
            self.logger.error(f"Failed to update from filled order : {order} ({e})")

    def update_portfolio_available_from_order(self, order, is_new_order=True):
        """
        Realise portfolio availability update
        :param order: the order that triggers the portfolio update
        :param is_new_order: True when the order is being created
        """
        pair_future_contract = order.exchange_manager.exchange.get_pair_future_contract(order.symbol)
        try:
            real_order_quantity = - (order.origin_quantity / pair_future_contract.current_leverage
                                     * (constants.ONE if is_new_order else -constants.ONE))

            # When inverse contract, decrease a currency market equivalent quantity from currency balance
            if pair_future_contract.is_inverse_contract():
                self._update_portfolio_data(order.currency, available_value=real_order_quantity / order.origin_price)

            # When non-inverse contract, decrease directly market quantity
            else:
                # decrease market quantity from market available balance
                self._update_portfolio_data(order.market, available_value=real_order_quantity * order.origin_price)
        except (decimal.DivisionByZero, decimal.InvalidOperation) as e:
            self.logger.error(f"Failed to update available from order : {order} ({e})")

    def update_portfolio_from_liquidated_position(self, position):
        """
        Update portfolio from liquidated position
        :param position: the liquidated position
        """
        try:
            new_quantity = -position.quantity / position.symbol_contract.current_leverage
            self._update_portfolio_data(position.currency
                                        if position.symbol_contract.is_inverse_contract() else position.market,
                                        total_value=new_quantity,
                                        available_value=new_quantity)
        except (decimal.DivisionByZero, decimal.InvalidOperation) as e:
            self.logger.error(f"Failed to update from liquidated position : {position} ({e})")
