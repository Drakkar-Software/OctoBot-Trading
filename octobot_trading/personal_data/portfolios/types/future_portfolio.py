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
            update_size, have_increased_position_size = position_instance.update_from_order(order)
            real_order_quantity = decimal.Decimal(update_size / pair_future_contract.current_leverage).copy_abs()

            # When inverse contract, decrease a currency market equivalent quantity from currency balance
            if pair_future_contract.is_inverse_contract():
                total_update_quantity = real_order_quantity / order.filled_price
                fees_update_quantity = -order.get_total_fees(order.currency)
                self._update_future_portfolio_data(
                    order.currency,
                    wallet_value=fees_update_quantity,
                    order_margin_value=-total_update_quantity,
                    position_margin_value=total_update_quantity if have_increased_position_size else constants.ZERO)

            # When non-inverse contract, decrease directly market quantity
            else:
                # decrease market quantity from market available balance
                total_update_quantity = real_order_quantity * order.filled_price
                fees_update_quantity = -order.get_total_fees(order.market)
                self._update_future_portfolio_data(
                    order.market,
                    wallet_value=fees_update_quantity,
                    order_margin_value=-total_update_quantity,
                    position_margin_value=total_update_quantity if have_increased_position_size else constants.ZERO)
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
            real_order_quantity = (order.origin_quantity / pair_future_contract.current_leverage
                                   * (constants.ONE if is_new_order else -constants.ONE))

            # When inverse contract, decrease a currency market equivalent quantity from currency balance
            if pair_future_contract.is_inverse_contract():
                self._update_future_portfolio_data(order.currency,
                                                   wallet_value=constants.ZERO,
                                                   position_margin_value=constants.ZERO,
                                                   order_margin_value=real_order_quantity / order.origin_price)
            # When non-inverse contract, decrease directly market quantity
            else:
                # decrease market quantity from market available balance
                self._update_future_portfolio_data(order.market,
                                                   wallet_value=constants.ZERO,
                                                   position_margin_value=constants.ZERO,
                                                   order_margin_value=real_order_quantity * order.origin_price)
        except (decimal.DivisionByZero, decimal.InvalidOperation) as e:
            self.logger.error(f"Failed to update available from order : {order} ({e})")

    def update_portfolio_from_liquidated_position(self, position):
        """
        Update portfolio from liquidated position
        :param position: the liquidated position
        """
        try:
            liquidated_quantity = -decimal.Decimal(
                position.get_quantity_to_close() / position.symbol_contract.current_leverage).copy_abs()
            if position.symbol_contract.is_inverse_contract():
                update_quantity = liquidated_quantity / position.mark_price
                self._update_future_portfolio_data(position.currency,
                                                   position_margin_value=update_quantity,
                                                   wallet_value=update_quantity)
            else:
                update_quantity = liquidated_quantity * position.mark_price
                self._update_future_portfolio_data(position.market,
                                                   position_margin_value=update_quantity,
                                                   wallet_value=update_quantity)
        except (decimal.DivisionByZero, decimal.InvalidOperation) as e:
            self.logger.error(f"Failed to update from liquidated position : {position} ({e})")

    def update_portfolio_from_funding(self, position, funding_rate):
        """
        Update portfolio from funding
        :param position: the perpetual position
        :param funding_rate: the funding rate
        """
        try:
            funding_fee = position.value * funding_rate
            # When inverse contract, decrease a currency market equivalent quantity from currency balance
            if position.symbol_contract.is_inverse_contract():
                self._update_future_portfolio_data(position.currency, wallet_value=-funding_fee)
            # When non-inverse contract, decrease directly market quantity
            else:
                self._update_future_portfolio_data(position.market, wallet_value=-funding_fee)
        except (decimal.DivisionByZero, decimal.InvalidOperation) as e:
            self.logger.error(f"Failed to update from funding : {position} ({e})")

    def update_portfolio_from_pnl(self, position):
        """
        Updates the portfolio from a Position PNL update
        :param position: position: the position instance with the new PNL
        """
        if position.symbol_contract.is_isolated():
            self.get_currency_portfolio(
                currency=position.currency if position.symbol_contract.is_inverse_contract() else position.market). \
                set_unrealized_pnl(position.unrealised_pnl)

    def _update_future_portfolio_data(self, currency,
                                      wallet_value=constants.ZERO,
                                      position_margin_value=constants.ZERO,
                                      order_margin_value=constants.ZERO,
                                      unrealized_pnl_value=constants.ZERO,
                                      initial_margin_value=constants.ZERO,
                                      replace_value=False):
        """
        Set new currency quantity in the portfolio
        :param currency: the currency to update
        :param wallet_value: the wallet balance value
        :param initial_margin_value: the initial margin value
        :param position_margin_value: the position margin value
        :param order_margin_value: the order margin value
        :param unrealized_pnl_value: the unrealized pnl value
        :param replace_value: when True replace the current value instead of updating it
        :return: True if updated
        """
        try:
            if replace_value:
                return self.portfolio[currency].set(total=wallet_value,
                                                    position_margin=position_margin_value,
                                                    initial_margin=initial_margin_value,
                                                    available=order_margin_value,
                                                    unrealized_pnl=unrealized_pnl_value)
            return self.portfolio[currency].update(total=wallet_value,
                                                   position_margin=position_margin_value,
                                                   initial_margin=initial_margin_value,
                                                   available=order_margin_value,
                                                   unrealized_pnl=unrealized_pnl_value)
        except KeyError:
            self.portfolio[currency] = self.create_currency_asset(currency=currency,
                                                                  available=order_margin_value,
                                                                  total=wallet_value)
            return True
