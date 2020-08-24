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
from octobot_commons.logging.logging_util import get_logger
from octobot_trading.channels.exchange_channel import get_chan
from octobot_trading.constants import CONFIG_SIMULATOR, \
    CONFIG_STARTING_PORTFOLIO, CURRENT_PORTFOLIO_STRING, BALANCE_CHANNEL
from octobot_trading.data.margin_portfolio import MarginPortfolio
from octobot_trading.data.portfolio import Portfolio
from octobot_trading.data.portfolio_profitability import PortfolioProfitabilty
from octobot_trading.util.initializable import Initializable


class PortfolioManager(Initializable):
    """
    Manage the portfolio and portfolio profitability instances
    """
    def __init__(self, config, trader, exchange_manager):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.config, self.trader, self.exchange_manager = config, trader, exchange_manager

        self.portfolio = None
        self.portfolio_profitability = None
        self.reference_market = None

    async def initialize_impl(self):
        """
        Reset the portfolio instance
        """
        await self._reset_portfolio()

    def handle_balance_update(self, balance):
        """
        Handle a balance update request
        :param balance: the new balance
        :return: True if the portfolio was updated
        """
        if self.trader.is_enabled and balance is not None:
            return self.portfolio.update_portfolio_from_balance(balance)
        return False

    async def handle_balance_update_from_order(self, order):
        """
        Handle a balance update from an order request
        :param order: the order
        :return: True if the portfolio was updated
        """
        if self.trader.is_enabled:
            if self.trader.simulate:
                if order.is_filled():
                    self.portfolio.update_portfolio_from_filled_order(order)
                else:
                    self.portfolio.update_portfolio_available(order, is_new_order=False)
                return True
            else:
                # on real trading: reload portfolio to ensure portfolio sync
                return await get_chan(BALANCE_CHANNEL, self.exchange_manager.id).get_internal_producer().\
                    refresh_real_trader_portfolio()
        return False

    async def _reset_portfolio(self):
        """
        Reset the portfolio and portfolio profitability instances
        """
        if self.exchange_manager.is_margin:
            self.portfolio = MarginPortfolio(self.exchange_manager.get_exchange_name(), self.trader.simulate)
        else:
            self.portfolio = Portfolio(self.exchange_manager.get_exchange_name(), self.trader.simulate)
        await self.portfolio.initialize()
        self._load_portfolio()

        self.portfolio_profitability = PortfolioProfitabilty(self.config, self.trader, self, self.exchange_manager)
        self.reference_market = self.portfolio_profitability.reference_market

    def _load_portfolio(self):
        """
        Load simulated portfolio from config if required
        """
        if self.trader.is_enabled:
            if self.trader.simulate:
                self._set_starting_simulated_portfolio()
            self.logger.info(f"{CURRENT_PORTFOLIO_STRING} {self.portfolio.portfolio}")

    def _set_starting_simulated_portfolio(self):
        """
        Load new portfolio from config settings
        """
        portfolio_amount_dict = self.config[CONFIG_SIMULATOR][CONFIG_STARTING_PORTFOLIO]

        try:
            self.handle_balance_update(self.portfolio.get_portfolio_from_amount_dict(portfolio_amount_dict))
        except Exception as e:
            self.logger.exception(e, True, f"Error when loading trading history, will reset history. ({e})")
            self.handle_balance_update(self.portfolio.get_portfolio_from_amount_dict(
                self.config[CONFIG_SIMULATOR][CONFIG_STARTING_PORTFOLIO]))
