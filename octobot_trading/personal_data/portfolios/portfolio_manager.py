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
import octobot_commons.logging as logging
import octobot_commons.constants as commons_constants

import octobot_trading.exchange_channel as exchange_channel
import octobot_trading.constants as constants
import octobot_trading.personal_data as personal_data
import octobot_trading.util as util


class PortfolioManager(util.Initializable):
    """
    Manage the portfolio and portfolio profitability instances
    """

    def __init__(self, config, trader, exchange_manager):
        super().__init__()
        self.logger = logging.get_logger(self.__class__.__name__)
        self.config, self.trader, self.exchange_manager = config, trader, exchange_manager

        self.portfolio = None
        self.portfolio_profitability = None
        self.portfolio_value_holder = None
        self.reference_market = None

    async def initialize_impl(self):
        """
        Reset the portfolio instance
        """
        await self._reset_portfolio()

    def handle_balance_update(self, balance, is_diff_update=False):
        """
        Handle a balance update request
        :param balance: the new balance
        :param is_diff_update: True when the update is a partial portfolio
        :return: True if the portfolio was updated
        """
        if self.trader.is_enabled and balance is not None:
            return self.portfolio.update_portfolio_from_balance(balance, force_replace=not is_diff_update)
        return False

    async def handle_balance_update_from_order(self, order) -> bool:
        """
        Handle a balance update from an order request
        :param order: the order
        :return: True if the portfolio was updated
        """
        if self.trader.is_enabled:
            if self.trader.simulate:
                return self._refresh_simulated_trader_portfolio_from_order(order)
            # on real trading: reload portfolio to ensure portfolio sync
            return await self._refresh_real_trader_portfolio()
        return False

    async def handle_balance_updated(self):
        """
        Handle balance update notification
        :return: True if profitability changed
        """
        return await self.portfolio_profitability.update_profitability()

    async def handle_profitability_recalculation(self, force_recompute_origin_portfolio):
        """
        Called before PortfolioProfitability's portfolio profitability recalculation
        to ensure portfolio values are available
        :param force_recompute_origin_portfolio: when True, force origin portfolio computation
        """
        await self.portfolio_value_holder.handle_profitability_recalculation(force_recompute_origin_portfolio)

    async def handle_mark_price_update(self, symbol, mark_price):
        """
        Handle a mark price update notification
        :param symbol: the update symbol
        :param mark_price: the updated mark price
        :return: True if profitability changed
        """
        return await self.portfolio_profitability. \
            update_profitability(force_recompute_origin_portfolio=self.portfolio_value_holder.
                                 update_origin_crypto_currencies_values(symbol, mark_price))

    async def _refresh_real_trader_portfolio(self) -> bool:
        """
        Call BALANCE_CHANNEL producer to refresh real trader portfolio
        :return: True if the portfolio was updated
        """
        return await exchange_channel.get_chan(constants.BALANCE_CHANNEL,
                                               self.exchange_manager.id).get_internal_producer().\
            refresh_real_trader_portfolio()

    async def _reset_portfolio(self):
        """
        Reset the portfolio and portfolio profitability instances
        """
        self.portfolio = personal_data.create_portfolio_from_exchange_manager(self.exchange_manager)
        await self.portfolio.initialize()
        self._load_portfolio()

        self.reference_market = util.get_reference_market(self.config)
        self.portfolio_value_holder = personal_data.PortfolioValueHolder(self)
        self.portfolio_profitability = personal_data.PortfolioProfitability(self)

    def _refresh_simulated_trader_portfolio_from_order(self, order):
        """
        Handle a balance update from an order request when simulating
        :param order: the order that should update portfolio
        :return: True if the portfolio was updated
        """
        if order.is_filled():
            self.portfolio.update_portfolio_from_filled_order(order)
        else:
            self.portfolio.update_portfolio_available(order, is_new_order=False)
        return True

    def _load_portfolio(self):
        """
        Load simulated portfolio from config if required
        """
        if self.trader.is_enabled:
            if self.trader.simulate:
                self._set_starting_simulated_portfolio()
            self.logger.info(f"{constants.CURRENT_PORTFOLIO_STRING} {self.portfolio.portfolio}")

    def _set_starting_simulated_portfolio(self):
        """
        Load new portfolio from config settings
        """
        portfolio_amount_dict = self.config[commons_constants.CONFIG_SIMULATOR][
            commons_constants.CONFIG_STARTING_PORTFOLIO]

        try:
            self.handle_balance_update(self.portfolio.get_portfolio_from_amount_dict(portfolio_amount_dict))
        except Exception as balance_update_exception:
            self.logger.exception(balance_update_exception, True, f"Error when loading trading history, "
                                                                  f"will reset history. ({balance_update_exception})")
            self.handle_balance_update(self.portfolio.get_portfolio_from_amount_dict(
                self.config[commons_constants.CONFIG_SIMULATOR][commons_constants.CONFIG_STARTING_PORTFOLIO]))

    def clear(self):
        """
        Clear portfolio manager objects
        """
        self.portfolio_profitability = None
        self.portfolio_value_holder = None
