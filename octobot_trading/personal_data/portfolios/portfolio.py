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
import copy
import decimal

import octobot_commons.constants as common_constants
import octobot_commons.logging as logging
import octobot_commons.asyncio_tools as asyncio_tools
import octobot_trading.constants as constants
import octobot_trading.enums as enums
import octobot_trading.util as util
import octobot_trading.personal_data as personal_data


class Portfolio(util.Initializable):
    """
    The Portfolio class manage an exchange portfolio
    This will begin by loading current exchange portfolio (by pulling user data)
    In case of simulation this will load the CONFIG_STARTING_PORTFOLIO
    This class also manage the availability of each currency in the portfolio:
    - When an order is created it will subtract the quantity of the total
    - When an order is filled or canceled restore the availability with the real quantity
    """

    def __init__(self, exchange_name, is_simulated=False):
        super().__init__()
        self._exchange_name = exchange_name
        self._is_simulated = is_simulated

        self.logger = logging.get_logger(
            f"{self.__class__.__name__}{'Simulator' if is_simulated else ''}[{exchange_name}]")
        self.lock = asyncio_tools.RLock()
        self.portfolio = None

    async def initialize_impl(self):
        """
        Initialize portfolio
        """
        self.reset()

    def reset(self):
        """
        Reset the portfolio dictionary
        """
        self.portfolio = {}

    async def copy(self):
        """
        Copy the portfolio object
        :return: the copied portfolio object
        """
        new_portfolio: Portfolio = Portfolio(self._exchange_name, self._is_simulated)
        await new_portfolio.initialize()
        new_portfolio.portfolio = copy.deepcopy(self.portfolio)
        return new_portfolio

    def update_portfolio_from_balance(self, balance, force_replace=True):
        """
        Update portfolio from a balance dict
        :param balance: the portfolio dict
        :param force_replace: force to update portfolio. Should be False when using deltas
        :return: True if the portfolio has been updated
        """
        if force_replace:
            self.portfolio = {
                currency: self._parse_raw_currency_asset(currency=currency, raw_currency_balance=balance[currency])
                for currency in balance}
            self.logger.debug(f"Portfolio updated | {constants.CURRENT_PORTFOLIO_STRING} {self}")
            return True
        if any(
                self._update_raw_currency_asset(currency=currency, raw_currency_balance=balance[currency])
                for currency in balance
        ):
            self.logger.debug(f"Portfolio partially updated | {constants.CURRENT_PORTFOLIO_STRING} {self}")
            return True
        return False

    def get_currency_portfolio(self, currency):
        """
        Get specified currency asset from portfolio
        :param currency: the currency to get
        :return: the currency portfolio asset instance
        """
        try:
            return self.portfolio[currency]
        except KeyError:
            self.portfolio[currency] = self.create_currency_asset(currency)
            return self.portfolio[currency]

    def create_currency_asset(self, currency, available=constants.ZERO, total=constants.ZERO):
        """
        Create the currency asset instance
        :param currency: the currency name
        :param available: the available value
        :param total: the total value
        :return: the currency asset instance
        """
        raise NotImplementedError("create_currency_asset is not implemented")

    def update_portfolio_data_from_order(self, order):
        """
        Call update_portfolio_data for order currency and market
        :param order: the order that updated the portfolio
        """
        raise NotImplementedError("update_portfolio_data_from_order is not implemented")

    def update_portfolio_available_from_order(self, order, is_new_order=True):
        """
        Realize portfolio availability update
        :param order: the order that triggers the portfolio update
        :param is_new_order: True when the order is being created
        """
        raise NotImplementedError("update_portfolio_available_from_order is not implemented")

    def update_portfolio_from_filled_order(self, order):
        """
        update_portfolio performs the update of the total / available quantity of a currency
        It is called only when an order is filled to update the real quantity of the currency to be set in "total" field
        :param order: the order to be taken into account
        """
        # stop losses and take profits aren't using available portfolio
        # restoring available portfolio when order type is stop loss or take profit
        if not _should_update_available(order):
            self.update_portfolio_available_from_order(order)

        self.update_portfolio_data_from_order(order)
        self.log_portfolio_update_from_order(order)

    def update_portfolio_available(self, order, is_new_order=False):
        """
        update_portfolio_available performs the availability update of the concerned currency in the current portfolio
        It is called when an order is filled, created or canceled to update the "available" filled of the portfolio
        is_new_order is True when portfolio needs an update after a new order and False when portfolio needs a rollback
        after an order is cancelled
        :param order: the order to take into account
        :param is_new_order: True if this is a new order
        :return: None
        """
        if _should_update_available(order):
            self.update_portfolio_available_from_order(order, is_new_order)

    def get_portfolio_from_amount_dict(self, amount_dict):
        """
        Create a portfolio from an amount dictionary
        :param amount_dict:
        :return: the portfolio dictionary
        """
        if not all(isinstance(i, decimal.Decimal) for i in amount_dict.values()):
            raise RuntimeError("Portfolio has to be initialized using decimal.Decimal")
        return {currency: self.create_currency_asset(currency=currency, available=total, total=total).to_dict()
                for currency, total in amount_dict.items()}

    def __str__(self):
        return f"{personal_data.portfolio_to_float(self.portfolio)}"

    def _update_portfolio_data(self, currency, total_value=constants.ZERO, available_value=constants.ZERO,
                               replace_value=False):
        """
        Set new currency quantity in the portfolio
        :param currency: the currency to update
        :param total_value: the total update value
        :param available_value: the available update value
        :param replace_value: when True replace the current value instead of updating it
        :return: True if updated
        """
        try:
            if replace_value:
                return self.portfolio[currency].set(available=available_value, total=total_value)
            return self.portfolio[currency].update(available=available_value, total=total_value)
        except KeyError:
            self.portfolio[currency] = self.create_currency_asset(currency=currency,
                                                                  available=available_value, total=total_value)
            return True

    def _parse_raw_currency_asset(self, currency, raw_currency_balance):
        """
        Parse the exchange currency balance as asset
        :param currency: the currency name
        :param raw_currency_balance: the raw current currency balance
        :return: the currency asset instance
        """
        available, total = _parse_raw_currency_balance(raw_currency_balance)
        return self.create_currency_asset(currency=currency, available=available, total=total)

    def _update_raw_currency_asset(self, currency, raw_currency_balance):
        """
        Update the exchange currency asset
        :param currency: the currency name
        :param raw_currency_balance: the raw current currency balance
        :return: True if updated
        """
        available, total = _parse_raw_currency_balance(raw_currency_balance)
        return self._update_portfolio_data(currency=currency, total_value=total,
                                           available_value=available, replace_value=True)

    def reset_portfolio_available(self, reset_currency=None, reset_quantity=None):
        """
        Resets available amount with total amount
        CAREFUL: if no currency is given, resets all the portfolio !
        :param reset_currency: the currency to be reset
        :param reset_quantity: the quantity to reset
        """
        if not reset_currency:
            self._reset_all_portfolio_available()
        else:
            if reset_currency in self.portfolio:
                self._reset_currency_portfolio_available(currency_to_reset=reset_currency,
                                                         reset_quantity=reset_quantity)

    def _reset_all_portfolio_available(self):
        """
        Reset all portfolio assets available value
        """
        for currency in self.portfolio:
            self.portfolio[currency].restore_available()

    def _reset_currency_portfolio_available(self, currency_to_reset, reset_quantity):
        """
        Reset currency portfolio to available
        :param currency_to_reset: the currency to reset
        :param reset_quantity: the quantity to reset
        """
        if reset_quantity is None:
            self.portfolio[currency_to_reset].restore_available()
        else:
            self.portfolio[currency_to_reset].update(available=reset_quantity)

    def log_portfolio_update_from_order(self, order):
        """
        Log a portfolio update from an order
        :param order: the order that updated the portfolio
        """
        if order.side == enums.TradeOrderSide.BUY:
            currency_portfolio_num = order.filled_quantity - order.get_total_fees(order.currency)
            market_portfolio_num = -order.filled_quantity * order.filled_price
        else:
            currency_portfolio_num = -order.filled_quantity
            market_portfolio_num = order.filled_quantity * order.filled_price - order.get_total_fees(order.market)

        self.logger.debug(f"Portfolio updated from order | {order.currency} {currency_portfolio_num} | {order.market} "
                          f"{market_portfolio_num} | {constants.CURRENT_PORTFOLIO_STRING} {self.portfolio}")


def _should_update_available(order):
    """
    Check if the order has impact on availability
    :param order: The order to check
    :return: True if the order should update available portfolio
    """
    return not order.is_self_managed()


def _parse_raw_currency_balance(raw_currency_balance):
    """
    Parse the exchange balance
    Set 0 as currency value when the parsed value is None (concerning available and total values)
    :param raw_currency_balance: the current currency balance
    :return: the currency available and total as tuple
    """
    return (raw_currency_balance.get(constants.CONFIG_PORTFOLIO_FREE,
                                     raw_currency_balance.get(common_constants.PORTFOLIO_AVAILABLE,
                                                              constants.ZERO)) or constants.ZERO,
            raw_currency_balance.get(constants.CONFIG_PORTFOLIO_TOTAL,
                                     raw_currency_balance.get(common_constants.PORTFOLIO_TOTAL,
                                                              constants.ZERO)) or constants.ZERO)
