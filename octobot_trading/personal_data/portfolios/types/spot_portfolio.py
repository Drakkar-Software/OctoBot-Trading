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


class SpotPortfolio(portfolio_class.Portfolio):
    def create_currency_asset(self, currency, available=constants.ZERO, total=constants.ZERO):
        return spot_asset.SpotAsset(name=currency, available=available, total=total)

    def update_portfolio_data_from_order(self, order):
        """
        Call update_portfolio_data for order currency and market
        :param order: the order that updated the portfolio
        """
        # update currency
        if order.side == enums.TradeOrderSide.BUY:
            new_quantity = order.filled_quantity - order.get_total_fees(order.currency)
            self._update_portfolio_data(order.currency, total_value=new_quantity, available_value=new_quantity)
        else:
            new_quantity = -order.filled_quantity
            self._update_portfolio_data(order.currency, total_value=new_quantity)

        # update market
        if order.side == enums.TradeOrderSide.BUY:
            new_quantity = -(order.filled_quantity * order.filled_price)
            self._update_portfolio_data(order.market, total_value=new_quantity)
        else:
            new_quantity = (order.filled_quantity * order.filled_price) - order.get_total_fees(order.market)
            self._update_portfolio_data(order.market, total_value=new_quantity, available_value=new_quantity)

    def update_portfolio_available_from_order(self, order, is_new_order=True):
        """
        Realise portfolio availability update
        :param order: the order that triggers the portfolio update
        :param is_new_order: True when the order is being created
        """
        # when buy order
        if order.side == enums.TradeOrderSide.BUY:
            new_quantity = - order.origin_quantity * order.origin_price * (constants.ONE if is_new_order else -constants.ONE)
            self._update_portfolio_data(order.market,
                                        available_value=new_quantity,
                                        total_value=constants.ZERO)

        # when sell order
        else:
            new_quantity = - order.origin_quantity * (constants.ONE if is_new_order else -constants.ONE)
            self._update_portfolio_data(order.currency,
                                        available_value=new_quantity,
                                        total_value=constants.ZERO)
