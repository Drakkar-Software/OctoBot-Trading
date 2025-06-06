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
import octobot_trading.personal_data.portfolios.assets.spot_asset as spot_asset
import octobot_trading.personal_data.portfolios.portfolio as portfolio_class
import octobot_trading.personal_data.orders.order_util as order_util


class SpotPortfolio(portfolio_class.Portfolio):
    def create_currency_asset(self, currency, available=constants.ZERO, total=constants.ZERO):
        return spot_asset.SpotAsset(name=currency, available=available, total=total)

    def update_portfolio_data_from_order(self, order):
        """
        Call update_portfolio_data for order currency and market
        :param order: the order that updated the portfolio
        """
        base_fees = order.get_total_fees(order.currency)
        quote_fees = order.get_total_fees(order.market)
        forecasted_fees = order.get_computed_fee(use_origin_quantity_and_price=True)
        forecasted_base_fees = order_util.get_fees_for_currency(forecasted_fees, order.currency)
        forecasted_quote_fees = order_util.get_fees_for_currency(forecasted_fees, order.market)

        # update base
        if order.side == enums.TradeOrderSide.BUY:
            new_quantity = order.filled_quantity - base_fees
            self._update_portfolio_data(order.currency, total_value=new_quantity, available_value=new_quantity)
        else:
            new_quantity = -order.filled_quantity - base_fees
            # Align available amount using really paid fees. Does nothing if forecasted fees == real fees
            available_update = forecasted_base_fees - base_fees
            self._update_portfolio_data(order.currency, total_value=new_quantity, available_value=available_update)

        # update quote
        if order.side == enums.TradeOrderSide.BUY:
            new_quantity = -(order.filled_quantity * order.filled_price) - quote_fees
            # Align available amount using really paid fees. Does nothing if forecasted fees == real fees
            available_update = forecasted_quote_fees - quote_fees
            self._update_portfolio_data(order.market, total_value=new_quantity, available_value=available_update)
        else:
            new_quantity = (order.filled_quantity * order.filled_price) - quote_fees
            self._update_portfolio_data(order.market, total_value=new_quantity, available_value=new_quantity)

    def update_portfolio_data_from_withdrawal(self, amount, currency):
        """
        Call update_portfolio_data for order currency and market
        :param amount: the withdrawal amount
        :param currency: the withdrawal currency
        """
        self._update_portfolio_data(currency, total_value=-amount)

    def update_portfolio_available_from_order(self, order, is_new_order=True):
        """
        Realize portfolio availability update
        :param order: the order that triggers the portfolio update
        :param is_new_order: True when the order is being created, False when canceled
        """
        multiplier = constants.ONE if is_new_order else -constants.ONE

        # force_use_origin_quantity_and_price is True here to ensure symetry between funds locked to open orders and
        # funds released orders are not open anymore
        new_quantity = -order_util.get_order_locked_amount(order, force_use_origin_quantity_and_price=True) * multiplier
        unit = order.market if order.side == enums.TradeOrderSide.BUY else order.currency
        self._update_portfolio_data(unit, available_value=new_quantity, total_value=constants.ZERO)
