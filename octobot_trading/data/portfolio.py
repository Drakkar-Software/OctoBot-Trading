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

from octobot_trading.util.initializable import Initializable
from octobot_trading.orders import OrderConstants

from octobot_trading.constants import CURRENT_PORTFOLIO_STRING, CONFIG_PORTFOLIO_FREE, CONFIG_PORTFOLIO_TOTAL
from octobot_trading.enums import TradeOrderSide, TraderOrderType
from octobot_commons.logging.logging_util import get_logger
from octobot_commons.constants import PORTFOLIO_AVAILABLE, PORTFOLIO_TOTAL

""" The Portfolio class manage an exchange portfolio
This will begin by loading current exchange portfolio (by pulling user data)
In case of simulation this will load the CONFIG_STARTING_PORTFOLIO
This class also manage the availability of each currency in the portfolio:
- When an order is created it will subtract the quantity of the total
- When an order is filled or canceled restore the availability with the real quantity """


class Portfolio(Initializable):
    def __init__(self, exchange_name, is_simulated=False):
        super().__init__()
        self.portfolio = {}
        self.logger = get_logger(
            f"{self.__class__.__name__}{'Simulator' if is_simulated else ''}[{exchange_name}]")
        self.lock = Lock()

    async def initialize_impl(self):
        self.portfolio = {}

    async def update_portfolio_from_balance(self, balance) -> bool:
        if balance == self.portfolio:
            return False
        self.portfolio = {currency: {PORTFOLIO_AVAILABLE: balance[currency][CONFIG_PORTFOLIO_FREE],
                                     PORTFOLIO_TOTAL: balance[currency][CONFIG_PORTFOLIO_TOTAL]}
                          for currency in balance}
        self.logger.info(f"Portfolio updated | {CURRENT_PORTFOLIO_STRING} {self.portfolio}")
        return False

    def get_currency_from_given_portfolio(self, currency, portfolio_type=PORTFOLIO_AVAILABLE):
        if currency in self.portfolio:
            return self.portfolio[currency][portfolio_type]
        self.portfolio[currency] = {
            PORTFOLIO_AVAILABLE: 0,
            PORTFOLIO_TOTAL: 0
        }
        return self.portfolio[currency][portfolio_type]

    # Get specified currency quantity in the portfolio
    def get_currency_portfolio(self, currency, portfolio_type=PORTFOLIO_AVAILABLE):
        return self.get_currency_from_given_portfolio(currency, portfolio_type)

    # Set new currency quantity in the portfolio
    def _update_portfolio_data(self, currency, value, total=True, available=False):
        if currency in self.portfolio:
            if total:
                self.portfolio[currency][PORTFOLIO_TOTAL] += value
            if available:
                self.portfolio[currency][PORTFOLIO_AVAILABLE] += value
        else:
            self.portfolio[currency] = {PORTFOLIO_AVAILABLE: value, PORTFOLIO_TOTAL: value}

    """ update_portfolio performs the update of the total / available quantity of a currency
    It is called only when an order is filled to update the real quantity of the currency to be set in "total" field
    Returns get_profitability() return
    """

    async def update_portfolio_from_order(self, order):
        # stop losses and take profits aren't using available portfolio
        if not self._check_available_should_update(order):
            self._update_portfolio_available(order)

        currency, market = order.get_currency_and_market()

        # update currency
        if order.side == TradeOrderSide.BUY:
            new_quantity = order.filled_quantity - order.get_total_fees(currency)
            self._update_portfolio_data(currency, new_quantity, True, True)
        else:
            new_quantity = -order.filled_quantity
            self._update_portfolio_data(currency, new_quantity, True, False)

        # update market
        if order.side == TradeOrderSide.BUY:
            new_quantity = -(order.filled_quantity * order.filled_price)
            self._update_portfolio_data(market, new_quantity, True, False)
        else:
            new_quantity = (order.filled_quantity * order.filled_price) - order.get_total_fees(market)
            self._update_portfolio_data(market, new_quantity, True, True)

        # Only for log purpose
        if order.side == TradeOrderSide.BUY:
            currency_portfolio_num = order.filled_quantity - order.get_total_fees(currency)
            market_portfolio_num = -order.filled_quantity * order.filled_price
        else:
            currency_portfolio_num = -order.filled_quantity
            market_portfolio_num = \
                order.filled_quantity * order.filled_price - order.get_total_fees(market)

        self.logger.info(f"Portfolio updated | {currency} {currency_portfolio_num} | {market} "
                         f"{market_portfolio_num} | {CURRENT_PORTFOLIO_STRING} {self.portfolio}")

    """ update_portfolio_available performs the availability update of the concerned currency in the current portfolio
    It is called when an order is filled, created or canceled to update the "available" filed of the portfolio
    is_new_order is True when portfolio needs an update after a new order and False when portfolio needs a rollback 
    after an order is cancelled
    """

    def update_portfolio_available(self, order, is_new_order=False):
        if self._check_available_should_update(order):
            self._update_portfolio_available(order, 1 if is_new_order else -1)

    # Check if the order has impact on availability
    def _check_available_should_update(self, order):
        # stop losses and take profits aren't using available portfolio
        return order.__class__ not in [OrderConstants.TraderOrderTypeClasses[TraderOrderType.STOP_LOSS],
                                       OrderConstants.TraderOrderTypeClasses[TraderOrderType.STOP_LOSS_LIMIT]]

    # Realise portfolio availability update
    def _update_portfolio_available(self, order, factor=1):
        currency, market = order.get_currency_and_market()

        # when buy order
        if order.side == TradeOrderSide.BUY:
            new_quantity = - order.origin_quantity * order.origin_price * factor
            self._update_portfolio_data(market, new_quantity, False, True)

        # when sell order
        else:
            new_quantity = - order.origin_quantity * factor
            self._update_portfolio_data(currency, new_quantity, False, True)

    # Resets available amount with total amount CAREFUL: if no currency is give, resets all the portfolio !
    def reset_portfolio_available(self, reset_currency=None, reset_quantity=None):
        if not reset_currency:
            self.portfolio.update({currency: {PORTFOLIO_AVAILABLE: self.portfolio[currency][PORTFOLIO_TOTAL],
                                              PORTFOLIO_TOTAL: self.portfolio[currency][PORTFOLIO_TOTAL]}
                                   for currency in self.portfolio})
        else:
            if reset_currency in self.portfolio:
                if reset_quantity is None:
                    self.portfolio[reset_currency][PORTFOLIO_AVAILABLE] = \
                        self.portfolio[reset_currency][PORTFOLIO_TOTAL]
                else:
                    self.portfolio[reset_currency][PORTFOLIO_AVAILABLE] += reset_quantity

    @staticmethod
    def get_portfolio_from_amount_dict(amount_dict):
        if not all(isinstance(i, (int, float)) for i in amount_dict.values()):
            raise RuntimeError("Portfolio has to be initialized using numbers")
        return {currency: {PORTFOLIO_AVAILABLE: total, PORTFOLIO_TOTAL: total}
                for currency, total in amount_dict.items()}
