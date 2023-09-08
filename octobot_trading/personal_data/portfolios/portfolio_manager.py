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
import contextlib
import copy

import octobot_commons.logging as logging
import octobot_commons.constants as commons_constants
import octobot_commons.tree as commons_tree
import octobot_commons.enums as commons_enums

import octobot_trading.exchange_channel as exchange_channel
import octobot_trading.constants as constants
import octobot_trading.errors as errors
import octobot_trading.personal_data as personal_data
import octobot_trading.util as util
import octobot_trading.enums as enums


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
        self.historical_portfolio_value_manager = None
        self.reference_market = None
        self._is_initialized_event_set = False
        self._forced_portfolio = None
        self._enable_portfolio_update_from_order = True

    async def initialize_impl(self):
        """
        Reset the portfolio instance
        """

        if (self.exchange_manager.is_storage_enabled() or self.exchange_manager.is_backtesting) \
                and self.historical_portfolio_value_manager is None:
            self.historical_portfolio_value_manager = personal_data.HistoricalPortfolioValueManager(self)
            await self.historical_portfolio_value_manager.initialize()
        self.set_forced_portfolio_initial_config(
            self.config[commons_constants.CONFIG_SIMULATOR][commons_constants.CONFIG_STARTING_PORTFOLIO]
        )
        self._reset_portfolio()

    def handle_balance_update(self, balance, is_diff_update=False):
        """
        Handle a balance update request
        :param balance: the new balance
        :param is_diff_update: True when the update is a partial portfolio
        :return: True if the portfolio was updated
        """
        changed = False
        if self.trader.is_enabled and balance is not None:
            changed = self.portfolio.update_portfolio_from_balance(balance, force_replace=not is_diff_update)
        if not self._is_initialized_event_set:
            self._set_initialized_event()
            self._is_initialized_event_set = True
        return changed

    async def handle_balance_update_from_order(self, order, require_exchange_update: bool) -> bool:
        """
        Handle a balance update from an order update
        :param order: the order
        :param require_exchange_update: when True, will sync with exchange portfolio, otherwise will predict the
        portfolio changes using order data (as in trading simulator)
        :return: True if the portfolio was updated
        """
        if self.trader.is_enabled and self._enable_portfolio_update_from_order:
            async with self.portfolio_history_update():
                if self.trader.simulate or not require_exchange_update:
                    return self._refresh_simulated_trader_portfolio_from_order(order)
                # on real trading only:
                # reload portfolio to ensure portfolio sync
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
            async with self.portfolio_history_update():
                if self.trader.simulate or not require_exchange_update:
                    self.portfolio.update_portfolio_from_funding(position, funding_rate)
                    return True
                # on real trading: reload portfolio to ensure portfolio sync
                return await self._refresh_real_trader_portfolio()
        return False

    async def handle_balance_update_from_withdrawal(self, amount, currency) -> bool:
        """
        Handle a balance update from a withdrawal update
        :param amount: the amount to withdraw
        :param currency: the currency to withdraw
        :return: True if the portfolio was updated
        """
        if self.trader.is_enabled:
            async with self.portfolio_history_update():
                if self.trader.simulate:
                    self.portfolio.update_portfolio_from_withdrawal(amount, currency)
                    return True
                # do not withdraw on real trading
                raise errors.PortfolioOperationError("withdraw is not supported in real trading")
        return False

    def handle_balance_updated(self):
        """
        Handle balance update notification
        :return: True if profitability changed
        """
        return self.portfolio_profitability.update_profitability()

    def get_portfolio_historical_values(self, currency, time_frame, from_timestamp, to_timestamp):
        if self.historical_portfolio_value_manager is None:
            raise errors.NotSupported("historical_portfolio_value_manager has to be set to get historical values")
        historical_values = self.historical_portfolio_value_manager.get_historical_values(
            currency, time_frame, from_timestamp, to_timestamp
        )
        # add/update current portfolio value
        current_historical_time = self.historical_portfolio_value_manager.convert_to_historical_timestamp(
            self.exchange_manager.exchange.get_exchange_current_time(), time_frame
        )
        if self.portfolio_value_holder is not None:
            historical_values[current_historical_time] = self.portfolio_value_holder.portfolio_current_value
        return [
            {
                enums.HistoricalPortfolioValue.TIME.value: key,
                enums.HistoricalPortfolioValue.VALUE.value: val,
            }
            for key, val in historical_values.items()
        ]

    async def update_historical_portfolio_values(self):
        if self.historical_portfolio_value_manager is None or \
           not self.portfolio_value_holder.current_crypto_currencies_values or \
           self.portfolio_value_holder.value_converter.initializing_symbol_prices:
            # initializing symbol prices, impossible to get an accurate portfolio value for now
            return
        try:
            # in backtesting, save at the end of the backtesting when calling stop
            await self.historical_portfolio_value_manager.on_new_value(
                self.exchange_manager.exchange.get_exchange_current_time(),
                {
                    self.reference_market: self.portfolio_value_holder.portfolio_current_value
                },
                save_changes=not self.exchange_manager.is_backtesting
            )
        except Exception as e:
            self.logger.exception(e, True, f"Error when saving historical portfolio: {e}")

    @contextlib.asynccontextmanager
    async def portfolio_history_update(self):
        try:
            yield
        finally:
            if self.historical_portfolio_value_manager is not None:
                try:
                    await self.historical_portfolio_value_manager.on_portfolio_update()
                except Exception as err:
                    self.logger.exception(err, True, f"Error when updating portfolio history: {err}")

    def handle_profitability_recalculation(self, force_recompute_origin_portfolio):
        """
        Called before PortfolioProfitability's portfolio profitability recalculation
        to ensure portfolio values are available
        :param force_recompute_origin_portfolio: when True, force origin portfolio computation
        """
        self.portfolio_value_holder.handle_profitability_recalculation(force_recompute_origin_portfolio)

    def handle_mark_price_update(self, symbol, mark_price):
        """
        Handle a mark price update notification
        :param symbol: the update symbol
        :param mark_price: the updated mark price in Decimal
        :return: True if profitability changed
        """
        return self.portfolio_profitability. \
            update_profitability(force_recompute_origin_portfolio=self.portfolio_value_holder.
                                 update_origin_crypto_currencies_values(symbol, mark_price))

    @contextlib.contextmanager
    def disabled_portfolio_update_from_order(self):
        """
        Can be used to locally disable portfolio refresh when an order is updated
        """
        self._enable_portfolio_update_from_order = False
        try:
            yield
        finally:
            self._enable_portfolio_update_from_order = True

    async def _refresh_real_trader_portfolio(self) -> bool:
        """
        Call BALANCE_CHANNEL producer to refresh real trader portfolio
        :return: True if the portfolio was updated
        """
        return await exchange_channel.get_chan(
            constants.BALANCE_CHANNEL, self.exchange_manager.id
        ).get_internal_producer().refresh_real_trader_portfolio()

    async def reset_history(self):
        if self.trader.simulate:
            # reset simulated portfolio
            # save not_available assets to reapply them
            previous_assets = self.portfolio.portfolio
            self._load_portfolio(True)
            self._apply_locked_assets(previous_assets)
        # nothing specific to do for real trader
        # reset values
        self.portfolio_value_holder.reset_portfolio_values()
        self.portfolio_profitability.reset_profitability()
        # reset historical values using now as a starting point
        if self.exchange_manager.is_storage_enabled():
            await self.historical_portfolio_value_manager.reset_history()

    def _apply_locked_assets(self, previous_assets):
        for key, asset in self.portfolio.portfolio.items():
            if key in previous_assets:
                asset.restore_unavailable_from_other(previous_assets[key])

    def _reset_portfolio(self):
        """
        Reset the portfolio and portfolio profitability instances
        """
        self.portfolio = personal_data.create_portfolio_from_exchange_manager(self.exchange_manager)
        self._load_portfolio(False)

        self.reference_market = util.get_reference_market(self.config)
        self.portfolio_value_holder = personal_data.PortfolioValueHolder(self)
        self.portfolio_profitability = personal_data.PortfolioProfitability(self)
        self._is_initialized_event_set = False

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
            self.logger.exception(portfolio_negative_value_error, True,
                                  f"Failed to update portfolio : {portfolio_negative_value_error} "
                                  f"for order {order.to_dict()}")
        return False

    def _load_portfolio(self, reset_from_config):
        """
        Load simulated portfolio from config if required
        """
        if self.trader.is_enabled:
            if self.trader.simulate:
                if reset_from_config \
                        or self.historical_portfolio_value_manager is None \
                        or not self.historical_portfolio_value_manager.has_previous_session_portfolio():
                    self.apply_forced_portfolio()
                else:
                    self._load_simulated_portfolio_from_history()
            self.logger.debug(f"{constants.CURRENT_PORTFOLIO_STRING} {self.portfolio.portfolio}")

    def _load_simulated_portfolio_from_history(self):
        portfolio_amount_dict = personal_data.parse_decimal_config_portfolio(
            {
                symbol: value
                for symbol, value in self.historical_portfolio_value_manager.historical_ending_portfolio.items()
            }
        )
        for asset_dict in portfolio_amount_dict.values():
            # ignore loaded available value as simulated orders are not kept throughout instance
            # and therefore can't lock funds
            asset_dict[commons_constants.PORTFOLIO_AVAILABLE] = asset_dict[commons_constants.PORTFOLIO_TOTAL]
        self.handle_balance_update(self.portfolio.get_portfolio_from_amount_dict(portfolio_amount_dict))

    def set_forced_portfolio_initial_config(self, portfolio_config):
        forced_portfolio_initial_config = copy.deepcopy(portfolio_config)
        # ensure free and total amounts are present
        for key in list(forced_portfolio_initial_config):
            if not isinstance(forced_portfolio_initial_config[key], dict):
                forced_portfolio_initial_config[key] = {
                    commons_constants.PORTFOLIO_AVAILABLE: forced_portfolio_initial_config[key],
                    commons_constants.PORTFOLIO_TOTAL: forced_portfolio_initial_config[key],
                }
        self._forced_portfolio = forced_portfolio_initial_config

    def apply_forced_portfolio(self):
        """
        Load new portfolio from config settings
        """
        portfolio_amount_dict = personal_data.parse_decimal_config_portfolio(self._forced_portfolio)
        self.handle_balance_update(self.portfolio.get_portfolio_from_amount_dict(portfolio_amount_dict))

    def _set_initialized_event(self):
        commons_tree.EventProvider.instance().trigger_event(
            self.exchange_manager.bot_id, commons_tree.get_exchange_path(
                self.exchange_manager.exchange_name,
                commons_enums.InitializationEventExchangeTopics.BALANCE.value
            )
        )

    async def stop(self):
        if self.historical_portfolio_value_manager is not None:
            await self.historical_portfolio_value_manager.stop()

    def clear(self):
        """
        Clear portfolio manager objects
        """
        self.portfolio_profitability = None
        self.portfolio_value_holder.clear()
        self.portfolio_value_holder = None
        self.historical_portfolio_value_manager = None
