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
from asyncio import Lock
from copy import deepcopy

from octobot_commons.constants import PORTFOLIO_AVAILABLE, PORTFOLIO_TOTAL
from octobot_commons.logging.logging_util import get_logger

from octobot_trading.constants import CURRENT_PORTFOLIO_STRING, CONFIG_PORTFOLIO_FREE, CONFIG_PORTFOLIO_TOTAL
from octobot_trading.enums import TraderOrderType
from octobot_trading.orders.types import TraderOrderTypeClasses
from octobot_trading.util.initializable import Initializable


class Portfolio(Initializable):
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

        self.logger = get_logger(f"{self.__class__.__name__}{'Simulator' if is_simulated else ''}[{exchange_name}]")
        self.lock = Lock()
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
        new_portfolio.portfolio = deepcopy(self.portfolio)
        return new_portfolio

    def update_portfolio_from_balance(self, balance):
        """
        Update portfolio from a balance dict
        :param balance: the portfolio dict
        :return: True if the portfolio has been updated
        """
        if balance == self.portfolio:
            # when the portfolio shouldn't be updated
            return False
        self.portfolio = {currency: self._parse_currency_balance(balance[currency]) for currency in balance}
        self.logger.debug(f"Portfolio updated | {CURRENT_PORTFOLIO_STRING} {self.portfolio}")
        return True

    def get_currency_from_given_portfolio(self, currency, portfolio_type=PORTFOLIO_AVAILABLE):
        """
        Get the currency quantity from the portfolio type
        :param currency: the currency to get quantity
        :param portfolio_type: the portfolio type
        :return: the currency quantity for the portfolio type
        """
        try:
            return self.portfolio[currency][portfolio_type]
        except KeyError:
            self._reset_currency_portfolio(currency)
            return self.portfolio[currency][portfolio_type]

    def get_currency_portfolio(self, currency, portfolio_type=PORTFOLIO_AVAILABLE):
        """
        Get specified currency quantity in the portfolio
        :param currency: the currency to get
        :param portfolio_type: the portfolio type to get
        :return: the currency portfolio type value
        """
        return self.get_currency_from_given_portfolio(currency, portfolio_type)

    def update_portfolio_data_from_order(self, order, currency, market):
        """
        Call update_portfolio_data for order currency and market
        :param order: the order that updated the portfolio
        :param currency: the order currency
        :param market: the order market
        """
        raise NotImplementedError("update_portfolio_data_from_order is not implemented")

    def update_portfolio_available_from_order(self, order, factor=1):
        """
        Realise portfolio availability update
        :param order: the order that triggers the portfolio update
        :param factor: should be 1 or -1 to increase or decrease available currency portfolio
        """
        raise NotImplementedError("update_portfolio_available_from_order is not implemented")

    def log_portfolio_update_from_order(self, order, currency, market):
        """
        Log a portfolio update from an order
        :param order: the order that updated the portfolio
        :param currency: the order currency
        :param market: the order market
        """
        raise NotImplementedError("log_portfolio_update_from_order is not implemented")

    def update_portfolio_from_filled_order(self, order):
        """
        update_portfolio performs the update of the total / available quantity of a currency
        It is called only when an order is filled to update the real quantity of the currency to be set in "total" field
        :param order: the order to be taken into account
        """
        # stop losses and take profits aren't using available portfolio
        if not _check_available_should_update(order):
            self.update_portfolio_available_from_order(order)

        currency, market = order.get_currency_and_market()
        self.update_portfolio_data_from_order(order, currency, market)
        self.log_portfolio_update_from_order(order, currency, market)

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
        if _check_available_should_update(order):
            self.update_portfolio_available_from_order(order, 1 if is_new_order else -1)

    def get_portfolio_from_amount_dict(self, amount_dict):
        """
        Create a portfolio from an amount dictionary
        :param amount_dict:
        :return: the portfolio dictionary
        """
        if not all(isinstance(i, (int, float)) for i in amount_dict.values()):
            raise RuntimeError("Portfolio has to be initialized using numbers")
        return {currency: self._create_currency_portfolio(available=total, total=total)
                for currency, total in amount_dict.items()}

    def _update_portfolio_data(self, currency, value, total=True, available=False):
        """
        Set new currency quantity in the portfolio
        :param currency: the currency to update
        :param value: the update value
        :param total: True if total part should be updated
        :param available: True if available part should be updated
        """
        if currency in self.portfolio:
            self._update_currency_portfolio(currency,
                                            available=value if available else 0,
                                            total=value if total else 0)
        else:
            self._set_currency_portfolio(currency=currency, available=value, total=value)

    def _parse_currency_balance(self, currency_balance):
        """
        Parse the exchange balance from the default ccxt format
        :param currency_balance: the current currency balance
        :return: the updated currency portfolio
        """
        return self._create_currency_portfolio(
            available=currency_balance.get(CONFIG_PORTFOLIO_FREE, currency_balance.get(PORTFOLIO_AVAILABLE, 0)),
            total=currency_balance.get(CONFIG_PORTFOLIO_TOTAL, currency_balance.get(PORTFOLIO_TOTAL, 0)))

    def _create_currency_portfolio(self, available, total):
        """
        Create the currency portfolio dictionary
        :param available: the available value
        :param total: the total value
        :return: the portfolio dictionary
        """
        return {PORTFOLIO_AVAILABLE: available, PORTFOLIO_TOTAL: total}

    def _reset_currency_portfolio(self, currency):
        """
        Reset the currency portfolio to 0
        :param currency: the currency to reset
        """
        self._set_currency_portfolio(currency=currency, available=0, total=0)

    def _set_currency_portfolio(self, currency, available, total):
        """
        Set the currency portfolio
        :param currency: the currency to set
        :param available: the available value
        :param total: the total value
        """
        self.portfolio[currency] = self._create_currency_portfolio(available=available, total=total)

    def _update_currency_portfolio(self, currency, available=0, total=0):
        """
        Update the currency portfolio
        :param currency: the currency to update
        :param available: the available delta
        :param total: the total delta
        """
        self.portfolio[currency][PORTFOLIO_AVAILABLE] += available
        self.portfolio[currency][PORTFOLIO_TOTAL] += total

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
        Reset all portfolio currencies to available
        """
        self.portfolio.update(
            {
                currency: self._create_currency_portfolio(
                    available=self.portfolio[currency][PORTFOLIO_TOTAL],
                    total=self.portfolio[currency][PORTFOLIO_TOTAL])
                for currency in self.portfolio
            })

    def _reset_currency_portfolio_available(self, currency_to_reset, reset_quantity):
        """
        Reset currency portfolio to available
        :param currency_to_reset: the currency to reset
        :param reset_quantity: the quantity to reset
        """
        if reset_quantity is None:
            self._set_currency_portfolio(currency=currency_to_reset,
                                         available=self.portfolio[currency_to_reset][PORTFOLIO_TOTAL],
                                         total=self.portfolio[currency_to_reset][PORTFOLIO_TOTAL])
        else:
            self._update_currency_portfolio(currency=currency_to_reset, available=reset_quantity)


def _check_available_should_update(order):
    """
    Check if the order has impact on availability
    :param order: The order to check
    :return: True if the order should update available portfolio
    """
    # stop losses and take profits aren't using available portfolio
    return order.__class__ not in [TraderOrderTypeClasses[TraderOrderType.STOP_LOSS],
                                   TraderOrderTypeClasses[TraderOrderType.STOP_LOSS_LIMIT],
                                   TraderOrderTypeClasses[TraderOrderType.TAKE_PROFIT],
                                   TraderOrderTypeClasses[TraderOrderType.TAKE_PROFIT_LIMIT],
                                   TraderOrderTypeClasses[TraderOrderType.TRAILING_STOP],
                                   TraderOrderTypeClasses[TraderOrderType.TRAILING_STOP_LIMIT]]
