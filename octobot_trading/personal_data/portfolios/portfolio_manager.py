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

import octobot_commons.logging as logging
import octobot_commons.constants as commons_constants

import octobot_trading.exchange_channel as exchange_channel
import octobot_trading.constants as constants
import octobot_trading.errors as errors
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

    async def handle_balance_update_from_order(self, order, require_exchange_update: bool) -> bool:
        """
        Handle a balance update from an order request
        :param order: the order
        :param require_exchange_update: when True, will sync with exchange portfolio, otherwise will predict the
        portfolio changes using order data (as in trading simulator)
        :return: True if the portfolio was updated
        """
        if self.trader.is_enabled:
            if self.trader.simulate or not require_exchange_update:
                return self._refresh_simulated_trader_portfolio_from_order(order)
            # on real trading: reload portfolio to ensure portfolio sync
            return await self._refresh_real_trader_portfolio()
        return False

    async def handle_balance_update_from_position(self, position, require_exchange_update: bool) -> bool:
        """
        Handle a balance update from an order request
        :param position: the position
        :param require_exchange_update: when True, will sync with exchange portfolio, otherwise will predict the
        portfolio changes using position data (as in trading simulator)
        :return: True if the portfolio was updated
        """
        if self.trader.is_enabled:
            if self.trader.simulate or not require_exchange_update:
                return self._refresh_simulated_trader_portfolio_from_position(position)
            # on real trading: reload portfolio to ensure portfolio sync
            return await self._refresh_real_trader_portfolio()
        return False

    async def handle_balance_update_from_funding(self, position, funding_rate, require_exchange_update: bool) -> bool:
        """
        Handle a balance update from a funding update
        :param position: the position
        :param funding_rate: the funding rate
        :param require_exchange_update: when True, will sync with exchange portfolio, otherwise will predict the
        portfolio changes using position data (as in trading simulator)
        :return: True if the portfolio was updated
        """
        if self.trader.is_enabled:
            if self.trader.simulate or not require_exchange_update:
                self.portfolio.update_portfolio_from_funding(position, funding_rate)
                return True
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
        :param mark_price: the updated mark price in float
        :return: True if profitability changed
        """
        return await self.portfolio_profitability. \
            update_profitability(force_recompute_origin_portfolio=self.portfolio_value_holder.
                                 update_origin_crypto_currencies_values(symbol, decimal.Decimal(str(mark_price))))

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
        Catch a PortfolioNegativeValueError when calling portfolio update method and returns False if raised
        :param order: the order that should update portfolio
        :return: True if the portfolio was updated
        """
        try:
            if order.is_filled():
                self.portfolio.update_portfolio_from_filled_order(order)
            else:
                self.portfolio.update_portfolio_available(order, is_new_order=False)
            return True
        except errors.PortfolioNegativeValueError as portfolio_negative_value_error:
            self.logger.exception(f"Failed to update portfolio : {portfolio_negative_value_error}")
        return False

    def _refresh_simulated_trader_portfolio_from_position(self, position):
        """
        Handle a balance update from an position request when simulating
        Catch a PortfolioNegativeValueError when calling portfolio update method and returns False if raised
        :param position: the position that should update portfolio
        :return: True if the portfolio was updated
        """
        try:
            if position.is_liquidated():
                self.portfolio.update_portfolio_from_liquidated_position(position)
            return True
        except errors.PortfolioNegativeValueError as portfolio_negative_value_error:
            self.logger.exception(f"Failed to update portfolio : {portfolio_negative_value_error}")
        return False

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
        portfolio_amount_dict = personal_data.parse_decimal_config_portfolio(
            self.config[commons_constants.CONFIG_SIMULATOR][commons_constants.CONFIG_STARTING_PORTFOLIO]
        )
        self.handle_balance_update(self.portfolio.get_portfolio_from_amount_dict(portfolio_amount_dict))

    def clear(self):
        """
        Clear portfolio manager objects
        """
        self.portfolio_profitability = None
        self.portfolio_value_holder = None
