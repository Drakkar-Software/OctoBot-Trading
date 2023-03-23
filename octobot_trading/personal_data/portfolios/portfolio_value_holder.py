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

import octobot_commons.logging as logging
import octobot_commons.symbols as symbol_util

import octobot_trading.constants as constants
import octobot_trading.errors as errors
import octobot_trading.personal_data.portfolios.value_converter as value_converter


class PortfolioValueHolder:
    """
    PortfolioValueHolder calculates the current and the origin portfolio value in reference market for each updates
    """

    def __init__(self, portfolio_manager):
        self.portfolio_manager = portfolio_manager
        self.logger = logging.get_logger(f"{self.__class__.__name__}"
                                         f"[{self.portfolio_manager.exchange_manager.exchange_name}]")
        self.value_converter = value_converter.ValueConverter(self.portfolio_manager)

        self.portfolio_origin_value = constants.ZERO
        self.portfolio_current_value = constants.ZERO

        # values in decimal.Decimal
        self.origin_portfolio = None

        # values in decimal.Decimal
        self.origin_crypto_currencies_values = {}
        self.current_crypto_currencies_values = {}

    def reset_portfolio_values(self):
        self.portfolio_origin_value = constants.ZERO
        self.portfolio_current_value = constants.ZERO

        self.origin_portfolio = None

        self.origin_crypto_currencies_values = {}
        self.current_crypto_currencies_values = {}

    def update_origin_crypto_currencies_values(self, symbol, mark_price):
        """
        Update origin cryptocurrencies value
        :param symbol: the symbol to update
        :param mark_price: the symbol mark price value in decimal.Decimal
        :return: True if the origin portfolio should be recomputed
        """
        currency, market = symbol_util.parse_symbol(symbol).base_and_quote()
        # update origin values if this price has relevant data regarding
        # the origin portfolio (using both quote and base)
        origin_crypto_currencies_with_values = set(self.origin_crypto_currencies_values.keys())
        origin_currencies_should_be_updated = (
            (
                currency not in origin_crypto_currencies_with_values
                and currency != self.portfolio_manager.reference_market
            )
            or
            (
                market not in origin_crypto_currencies_with_values
                and market != self.portfolio_manager.reference_market
            )
        )
        self.value_converter.update_last_price(symbol, mark_price)
        if origin_currencies_should_be_updated:
            # Will fail if symbol doesn't have a price in
            # self.origin_crypto_currencies_values and therefore
            # requires the origin portfolio value to be recomputed 
            # using this price info in case this price is relevant
            if market == self.portfolio_manager.reference_market:
                self.origin_crypto_currencies_values[currency] = mark_price
            elif currency == self.portfolio_manager.reference_market:
                self.origin_crypto_currencies_values[market] = constants.ONE / mark_price
            else:
                try:
                    converted_value = self.value_converter.try_convert_currency_value_using_multiple_pairs(
                        currency, self.portfolio_manager.reference_market, constants.ONE, []
                    )
                    if converted_value is not None:
                        self.origin_crypto_currencies_values[currency] = converted_value
                except (errors.MissingPriceDataError, errors.PendingPriceDataError):
                    pass
        return origin_currencies_should_be_updated

    def get_current_crypto_currencies_values(self):
        """
        Return the current crypto-currencies values
        :return: the current crypto-currencies values
        """
        if not self.current_crypto_currencies_values:
            self._update_portfolio_and_currencies_current_value()
        return self.current_crypto_currencies_values

    def get_current_holdings_values(self):
        """
        Get holdings ratio for each currency
        :return: the holdings ratio dictionary
        """
        holdings = self.get_current_crypto_currencies_values()
        return {
            currency: self._get_currency_value(self.portfolio_manager.portfolio.portfolio, currency, holdings)
            for currency in holdings.keys()
        }

    def get_currency_holding_ratio(self, currency):
        """
        Return the holdings ratio for the specified currency
        :return: the holdings ratio
        """
        if self.portfolio_current_value:
            return self.value_converter.evaluate_value(
                currency,
                self.portfolio_manager.portfolio.get_currency_portfolio(currency).total
            ) / self.portfolio_current_value
        return constants.ZERO

    def handle_profitability_recalculation(self, force_recompute_origin_portfolio):
        """
        Initialize values required by portfolio profitability to perform its profitability calculation
        :param force_recompute_origin_portfolio: when True, force origin portfolio computation
        """
        self._update_portfolio_and_currencies_current_value()
        self._init_portfolio_values_if_necessary(force_recompute_origin_portfolio)

    def get_origin_portfolio_current_value(self, refresh_values=False):
        """
        Calculates and return the origin portfolio actual value
        :param refresh_values: when True, force origin portfolio reevaluation
        :return: the origin portfolio current value
        """
        if refresh_values:
            self.current_crypto_currencies_values.update(
                self._evaluate_config_crypto_currencies_and_portfolio_values(self.origin_portfolio.portfolio)
            )
        return self._update_portfolio_current_value(
            self.origin_portfolio.portfolio, currencies_values=self.current_crypto_currencies_values
        )

    def _init_portfolio_values_if_necessary(self, force_recompute_origin_portfolio):
        """
        Init origin portfolio values if necessary
        :param force_recompute_origin_portfolio: when True, force origin portfolio computation
        """
        if self.portfolio_origin_value == constants.ZERO:
            # try to update portfolio origin value if it's not known yet
            self._init_origin_portfolio_and_currencies_value()
        if force_recompute_origin_portfolio:
            self._recompute_origin_portfolio_initial_value()

    def _init_origin_portfolio_and_currencies_value(self):
        """
        Initialize origin portfolio and the origin portfolio currencies values
        """
        self.origin_portfolio = self.origin_portfolio or copy.copy(self.portfolio_manager.portfolio)
        self.origin_crypto_currencies_values.update(
            self._evaluate_config_crypto_currencies_and_portfolio_values(
                self.origin_portfolio.portfolio,
                ignore_missing_currency_data=True
            )
        )
        self._recompute_origin_portfolio_initial_value()

    def _update_portfolio_current_value(self, portfolio, currencies_values=None, fill_currencies_values=False):
        """
        Update the portfolio with current prices
        :param portfolio: the portfolio to update
        :param currencies_values: the currencies values
        :param fill_currencies_values: the currencies values to calculate
        :return: the updated portfolio
        """
        values = currencies_values
        if values is None or fill_currencies_values:
            value_update = self._evaluate_config_crypto_currencies_and_portfolio_values(portfolio)
            self.current_crypto_currencies_values.update(value_update)
            if len(self.current_crypto_currencies_values) > len(self.origin_crypto_currencies_values):
                # add any missing value to origin_crypto_currencies_values (can happen with indirect valuations)
                self._fill_currencies_values(self.origin_crypto_currencies_values)
            if fill_currencies_values:
                self._fill_currencies_values(currencies_values)
            values = self.current_crypto_currencies_values
        return self._evaluate_portfolio_value(portfolio, values)

    def _fill_currencies_values(self, currencies_values):
        """
        Fill a currency values dict with new data
        :param currencies_values: currencies values dict to be filled
        """
        currencies_values.update({
            currency: value
            for currency, value in self.current_crypto_currencies_values.items()
            if currency not in currencies_values
        })

    def _update_portfolio_and_currencies_current_value(self):
        """
        Update the portfolio current value with the current portfolio instance
        """
        self.portfolio_current_value = self._update_portfolio_current_value(
            self.portfolio_manager.portfolio.portfolio)

    def _recompute_origin_portfolio_initial_value(self):
        """
        Compute origin portfolio initial value and update portfolio_origin_value
        """
        if self.portfolio_manager.historical_portfolio_value_manager is not None \
           and self.portfolio_manager.historical_portfolio_value_manager.has_historical_starting_portfolio_value(
            self.portfolio_manager.reference_market
        ):
            # get origin value from history when possible
            value = self.portfolio_manager.historical_portfolio_value_manager.\
                get_historical_starting_starting_portfolio_value(self.portfolio_manager.reference_market)
            if value is not None:
                self.portfolio_origin_value = value
                return
        self.portfolio_origin_value = self._update_portfolio_current_value(
            self.origin_portfolio.portfolio,
            currencies_values=self.origin_crypto_currencies_values,
            fill_currencies_values=True
        )

    def _evaluate_config_crypto_currencies_and_portfolio_values(self,
                                                                portfolio,
                                                                ignore_missing_currency_data=False):
        """
        Evaluate both config and portfolio currencies values
        :param portfolio: the current portfolio
        :param ignore_missing_currency_data: when True, ignore missing currencies values in calculation
        :return: the result of config and portfolio currencies values calculation
        """
        evaluated_pair_values = {}
        evaluated_currencies = set()
        missing_tickers = set()

        self._evaluate_config_currencies_values(evaluated_pair_values, evaluated_currencies, missing_tickers)
        self._evaluate_portfolio_currencies_values(portfolio, evaluated_pair_values, evaluated_currencies,
                                                   missing_tickers, ignore_missing_currency_data)
        return evaluated_pair_values

    def _evaluate_config_currencies_values(self, evaluated_pair_values, evaluated_currencies, missing_tickers):
        """
        Evaluate config currencies values
        :param evaluated_pair_values: the list of evaluated pairs
        :param evaluated_currencies: the list of evaluated currencies
        :param missing_tickers: the list of missing currencies
        """
        if self.portfolio_manager.exchange_manager.exchange_config.traded_symbols:
            currency, market = \
                self.portfolio_manager.exchange_manager.exchange_config.traded_symbols[0].base_and_quote()
            currency_to_evaluate = currency
            try:
                if currency not in evaluated_currencies:
                    evaluated_pair_values[currency] = self.value_converter.evaluate_value(currency, constants.ONE)
                    evaluated_currencies.add(currency)
                if market not in evaluated_currencies:
                    currency_to_evaluate = market
                    evaluated_pair_values[market] = self.value_converter.evaluate_value(market, constants.ONE)
                    evaluated_currencies.add(market)
            except errors.MissingPriceDataError:
                missing_tickers.add(currency_to_evaluate)

    def _evaluate_portfolio_currencies_values(self,
                                              portfolio,
                                              evaluated_pair_values,
                                              evaluated_currencies,
                                              missing_tickers,
                                              ignore_missing_currency_data):
        """
        Evaluate current portfolio currencies values
        :param portfolio: the current portfolio
        :param evaluated_pair_values: the list of evaluated pairs
        :param evaluated_currencies: the list of evaluated currencies
        :param missing_tickers: the list of missing currencies
        :param ignore_missing_currency_data: when True, ignore missing currencies values in calculation
        """
        for currency in portfolio:
            try:
                if currency not in evaluated_currencies and self._should_currency_be_considered(
                        currency, portfolio, ignore_missing_currency_data
                ):
                    evaluated_pair_values[currency] = self.value_converter.evaluate_value(currency, constants.ONE)
                    evaluated_currencies.add(currency)
            except errors.MissingPriceDataError:
                missing_tickers.add(currency)

    def _evaluate_portfolio_value(self, portfolio, currencies_values=None):
        """
        Perform evaluate_value with a portfolio configuration
        :param portfolio: the portfolio to explore
        :param currencies_values: currencies to evaluate
        :return: the calculated quantity value in reference (attribute) currency
        """
        return sum([
            self._get_currency_value(portfolio, currency, currencies_values)
            for currency in portfolio
            if currency not in self.value_converter.missing_currency_data_in_exchange
        ])

    def _get_currency_value(self, portfolio, currency, currencies_values=None, raise_error=False):
        """
        Return the currency value
        :param portfolio: the specified portfolio
        :param currency: the currency to evaluate
        :param currencies_values: currencies values dict
        :param raise_error: When True, forward exceptions
        :return: the currency value
        """
        if currency in portfolio and portfolio[currency].total != constants.ZERO:
            if currencies_values and currency in currencies_values:
                return currencies_values[currency] * portfolio[currency].total
            return self.value_converter.evaluate_value(currency, portfolio[currency].total, raise_error)
        return constants.ZERO

    def _should_currency_be_considered(self, currency, portfolio, ignore_missing_currency_data):
        """
        Return True if enough data is available to evaluate currency value
        :param currency: the currency to evaluate
        :param portfolio: the specified portfolio
        :param ignore_missing_currency_data: When True, ignore check of currency presence
        in missing_currency_data_in_exchange
        :return: True if enough data is available to evaluate currency value
        """
        return (
            currency not in self.value_converter.missing_currency_data_in_exchange or ignore_missing_currency_data
        ) and (
            portfolio[currency].total > constants.ZERO
            or currency in self.portfolio_manager.portfolio_profitability.valuated_currencies
        )

    def clear(self):
        self.value_converter.clear()
        self.value_converter = None
        self.portfolio_manager = None
