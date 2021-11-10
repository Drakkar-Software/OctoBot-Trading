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
        # Don't update if order filled quantity is null
        if order.filled_quantity == 0:
            return False

        pair_future_contract = order.exchange_manager.exchange.get_pair_future_contract(order.symbol)
        position_instance = order.exchange_manager.exchange_personal_data.positions_manager. \
            get_order_position(order, contract=pair_future_contract)

        try:
            update_size, have_increased_position_size = position_instance.update_size_from_order(order=order)
            real_order_quantity = decimal.Decimal(update_size / pair_future_contract.current_leverage).copy_abs()

            # When inverse contract, decrease a currency market equivalent quantity from currency balance
            if pair_future_contract.is_inverse_contract():
                total_update_quantity = real_order_quantity / order.filled_price
                self._update_portfolio_data(order.currency,
                                            available_value=constants.ZERO
                                            if have_increased_position_size else total_update_quantity,
                                            total_value=-order.get_total_fees(order.currency))

            # When non-inverse contract, decrease directly market quantity
            else:
                # decrease market quantity from market available balance
                total_update_quantity = real_order_quantity * order.filled_price
                self._update_portfolio_data(order.market,
                                            available_value=constants.ZERO
                                            if have_increased_position_size else total_update_quantity,
                                            total_value=-order.get_total_fees(order.currency))
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
                self._update_portfolio_data(order.currency,
                                            available_value=real_order_quantity / order.origin_price,
                                            total_value=constants.ZERO)
            # When non-inverse contract, decrease directly market quantity
            else:
                # decrease market quantity from market available balance
                self._update_portfolio_data(order.market,
                                            available_value=real_order_quantity * order.origin_price,
                                            total_value=constants.ZERO)
        except (decimal.DivisionByZero, decimal.InvalidOperation) as e:
            self.logger.error(f"Failed to update available from order : {order} ({e})")

    def update_portfolio_from_liquidated_position(self, position):
        """
        Update portfolio from liquidated position
        :param position: the liquidated position
        """
        try:
            liquidated_quantity = position.get_quantity_to_close() / position.symbol_contract.current_leverage
            if position.symbol_contract.is_inverse_contract():
                self._update_portfolio_data(position.currency,
                                            available_value=-liquidated_quantity / position.mark_price,
                                            total_value=constants.ZERO)
            else:
                self._update_portfolio_data(position.market,
                                            available_value=-liquidated_quantity * position.mark_price,
                                            total_value=constants.ZERO)
        except (decimal.DivisionByZero, decimal.InvalidOperation) as e:
            self.logger.error(f"Failed to update from liquidated position : {position} ({e})")

    def update_portfolio_from_funding(self, position, funding_rate):
        """
        Update portfolio from funding
        :param position: the position
        :param funding_rate: the funding rate
        """
        try:
            funding_fee = position.value * funding_rate
            # When inverse contract, decrease a currency market equivalent quantity from currency balance
            if position.symbol_contract.is_inverse_contract():
                self._update_portfolio_data(position.currency,
                                            available_value=-funding_fee,
                                            total_value=-funding_fee)
            # When non-inverse contract, decrease directly market quantity
            else:
                self._update_portfolio_data(position.market,
                                            available_value=-funding_fee,
                                            total_value=-funding_fee)
        except (decimal.DivisionByZero, decimal.InvalidOperation) as e:
            self.logger.error(f"Failed to update from funding : {position} ({e})")
