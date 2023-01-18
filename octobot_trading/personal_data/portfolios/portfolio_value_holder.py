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
import asyncio
import copy
import decimal

import octobot_commons.logging as logging
import octobot_commons.symbols as symbol_util
import octobot_trading.api.symbol_data as symbol_data

import octobot_trading.constants as constants
import octobot_trading.errors as errors


class PortfolioValueHolder:
    """
    PortfolioValueHolder calculates the current and the origin portfolio value in reference market for each updates
    """

    def __init__(self, portfolio_manager):
        self.portfolio_manager = portfolio_manager
        self.logger = logging.get_logger(f"{self.__class__.__name__}"
                                         f"[{self.portfolio_manager.exchange_manager.exchange_name}]")

        self.initializing_symbol_prices = set()
        self.initializing_symbol_prices_pairs = set()

        self.portfolio_origin_value = constants.ZERO
        self.portfolio_current_value = constants.ZERO

        # values in decimal.Decimal
        self.last_prices_by_trading_pair = {}
        self.origin_portfolio = None

        # values in decimal.Decimal
        self.origin_crypto_currencies_values = {}
        self.current_crypto_currencies_values = {}

        # set of currencies for which the current exchange is not providing any suitable price data
        self.missing_currency_data_in_exchange = set()

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
        # update origin values if this price has relevant data regarding the origin portfolio (using both quote and base)
        origin_crypto_currencies_with_values \
            = set(self.origin_crypto_currencies_values.keys())
        origin_currencies_should_be_updated = (
                currency not in  origin_crypto_currencies_with_values
                or market not in origin_crypto_currencies_with_values
        )
        self.last_prices_by_trading_pair[symbol] = mark_price
        if origin_currencies_should_be_updated:
            # will fail if symbol doesn't have a price in 
            #   self.origin_crypto_currencies_values and therefore
            # requires the origin portfolio value to be recomputed 
            #   using this price info in case this price is relevant
            if market == self.portfolio_manager.reference_market:
                self.origin_crypto_currencies_values[currency] = mark_price
            elif currency == self.portfolio_manager.reference_market:
                self.origin_crypto_currencies_values[market] = (
                    constants.ONE / mark_price)
            else:
                converted_value = self.try_convert_currency_value_using_multiple_pairs (
                    currency, constants.ONE)
                if converted_value is not None:
                    self.origin_crypto_currencies_values[currency] = converted_value
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
        Get holdings ratio for each currencies
        :return: the holdings ratio dictionary
        """
        holdings = self.get_current_crypto_currencies_values()
        return {currency: self._get_currency_value(self.portfolio_manager.portfolio.portfolio, currency, holdings)
                for currency in holdings.keys()}

    def get_currency_holding_ratio(self, currency):
        """
        Return the holdings ratio for the specified currency
        :param currency: the currency
        :return: the holdings ratio
        """
        return self._evaluate_value(currency,
                                    self.portfolio_manager.portfolio.get_currency_portfolio(
                                        currency).total) / self.portfolio_current_value \
            if self.portfolio_current_value else constants.ZERO

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
                self._evaluate_config_crypto_currencies_and_portfolio_values(self.origin_portfolio.portfolio))
        return self._update_portfolio_current_value(self.origin_portfolio.portfolio,
                                                    currencies_values=self.current_crypto_currencies_values)

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
            self._evaluate_config_crypto_currencies_and_portfolio_values(self.origin_portfolio.portfolio,
                                                                         ignore_missing_currency_data=True))
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
            self.current_crypto_currencies_values.update(
                self._evaluate_config_crypto_currencies_and_portfolio_values(portfolio))
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

    def _evaluate_value(self, currency, quantity, raise_error=True):
        """
        Evaluate value returns the currency quantity value in the reference (attribute) currency
        :param currency: the currency to evaluate
        :param quantity: the currency quantity
        :param raise_error: will catch exception if False
        :return: the currency value
        """
        # easy case --> the current currency is the reference currency or the quantity is 0
        if currency == self.portfolio_manager.reference_market or quantity == constants.ZERO:
            return quantity
        currency_value = self._try_get_value_of_currency(currency, quantity, raise_error)
        return self._check_currency_initialization(currency=currency, currency_value=currency_value)

    def _check_currency_initialization(self, currency, currency_value):
        """
        Check if the currency has to be removed from self.initializing_symbol_prices and return currency_value
        :param currency: the currency to check
        :param currency_value: the currency value
        :return: currency_value after checking
        """
        if currency_value > constants.ZERO and currency in self.initializing_symbol_prices:
            self.initializing_symbol_prices.remove(currency)
        return currency_value

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
        self.portfolio_origin_value = \
            self._update_portfolio_current_value(self.origin_portfolio.portfolio,
                                                 currencies_values=self.origin_crypto_currencies_values,
                                                 fill_currencies_values=True)

    def _try_get_value_of_currency(self, currency, quantity, raise_error):
        """
        try_get_value_of_currency will try to obtain the current value of
            the currency quantity in reference currency.
        It will try to create the symbol that fit with the exchange logic.
        :return: the value found of this currency quantity, if not found returns 0.
        """
        settlement_asset = None
        if self.portfolio_manager.exchange_manager.is_future:
            settlement_asset = self.portfolio_manager.reference_market
        try:
            return self.convert_currency_value_using_last_prices(quantity, currency,
                                                                 self.portfolio_manager.reference_market,
                                                                 settlement_asset)
        except errors.MissingPriceDataError as missing_data_exception:
            if not self.portfolio_manager.exchange_manager.is_future:
                try:
                    value = self.try_convert_currency_value_using_multiple_pairs (currency, quantity)
                    if value is not None:
                        return value
                except errors.MissingPriceDataError:
                    pass
            symbol = symbol_util.merge_currencies(
                currency, self.portfolio_manager.reference_market,
                settlement_asset=settlement_asset)
            reversed_symbol = symbol_util.merge_currencies(
                self.portfolio_manager.reference_market, currency,
                settlement_asset=settlement_asset)
            if not any(self.portfolio_manager.exchange_manager.symbol_exists(s)
                       for s in (symbol, reversed_symbol)) \
               and currency not in self.missing_currency_data_in_exchange:
                self._inform_no_matching_symbol(currency)
                self.missing_currency_data_in_exchange.add(currency)
            if not self.portfolio_manager.exchange_manager.is_backtesting:
                self._try_to_ask_ticker_missing_symbol_data(currency, symbol, reversed_symbol)
                if raise_error:
                    raise missing_data_exception
        return constants.ZERO

    def convert_currency_value_using_last_prices(
        self, quantity, current_currency, target_currency, settlement_asset=None):
        try:
            symbol = symbol_util.merge_currencies(
                current_currency, target_currency, settlement_asset=settlement_asset)
            if self._has_price_data(symbol):
                return quantity * self._get_last_price_data(symbol)
        except KeyError:
            pass
        try:
            reversed_symbol = symbol_util.merge_currencies(target_currency, current_currency)
            return quantity / self._get_last_price_data(reversed_symbol)
        except decimal.DivisionByZero:
            pass
        except KeyError:
            pass
        raise errors.MissingPriceDataError(
            f"no price data to evaluate {current_currency} price in {target_currency}")

    def try_convert_currency_value_using_multiple_pairs (
        self, currency, quantity) -> decimal.Decimal:
        # settlement_asset needs to be handled to add support for futures
                
        # try with two pairs
        # for example:
        # currency: ETH - ref market: USDT
        #                   BTC/ETH      ->    BTC/USDT
        # first convert ETH -> BTC and then BTC -> USDT
        for symbol_str in symbol_data.get_config_symbols(
            self.portfolio_manager.exchange_manager.config, True
        ):
            parsed_symbol = symbol_util.parse_symbol(symbol_str)
            if parsed_symbol.base == currency:
                first_ref_market = parsed_symbol.quote
                second_symbol_str = symbol_util.merge_currencies(
                    first_ref_market, self.portfolio_manager.reference_market
                )
                try:
                    first_ref_market_value = (
                        self.convert_currency_value_using_last_prices(
                            quantity, currency, first_ref_market
                        )
                    )
                except errors.MissingPriceDataError:
                    # first pair might not be initialized
                    # or is not available at all
                    continue  # trying with other pairs
                if first_ref_market_value:
                    # check if second pair is available
                    if self.portfolio_manager.exchange_manager.symbol_exists(
                        second_symbol_str
                    ):
                        try:
                            ref_market_value = (
                                self.convert_currency_value_using_last_prices(
                                    first_ref_market_value,
                                    first_ref_market,
                                    self.portfolio_manager.reference_market,
                                )
                            )
                            if ref_market_value:
                                if currency in self.missing_currency_data_in_exchange:
                                    self.missing_currency_data_in_exchange.remove(currency)
                                return ref_market_value
                        except errors.MissingPriceDataError:
                            # conversion pairs might not be initialized
                            # or is not available at all
                            pass  # continue trying with reversed pair
                    # try reversed second pair
                    reversed_second_symbol_str = symbol_util.merge_currencies(
                        self.portfolio_manager.reference_market, first_ref_market
                    )
                    if self.portfolio_manager.exchange_manager.symbol_exists(
                        reversed_second_symbol_str
                    ):
                        try:
                            conversion_value = (
                                self.convert_currency_value_using_last_prices(
                                    constants.ONE,
                                    self.portfolio_manager.reference_market,
                                    first_ref_market,
                                )
                            )
                            if conversion_value:
                                if currency in self.missing_currency_data_in_exchange:
                                    self.missing_currency_data_in_exchange.remove(currency)
                                return first_ref_market_value / conversion_value
                        except errors.MissingPriceDataError:
                            # conversion pairs might not be initialized
                            # or is not available at all
                            pass  # continue trying with other pairs
        return None

    def _has_price_data(self, symbol):
        return self._get_last_price_data(symbol) is not constants.ZERO

    def _get_last_price_data(self, symbol):
        try:
            return self.last_prices_by_trading_pair[symbol]
        except KeyError:
            # a settlement asset or other symbol extra 
            # data might be different, try to ignore it
            to_find_symbol = symbol_util.parse_symbol(symbol)
            for symbol_key, this_last_prices \
                in self.last_prices_by_trading_pair.items():
                if symbol_util.parse_symbol(
                    symbol_key).is_same_base_and_quote(to_find_symbol):
                    return this_last_prices
        raise KeyError(symbol)

    def _try_to_ask_ticker_missing_symbol_data(self, currency, symbol, reversed_symbol):
        """
        Try to ask the ticker producer to watch additional symbols
        to collect missing data required for profitability calculation
        :param currency: the concerned currency
        :param symbol: the symbol to add
        :param reversed_symbol: the reversed symbol to add
        """
        symbols_to_add = []
        if self.portfolio_manager.exchange_manager.symbol_exists(symbol):
            symbols_to_add = [symbol]
        elif self.portfolio_manager.exchange_manager.symbol_exists(reversed_symbol):
            symbols_to_add = [reversed_symbol]

        new_symbols_to_add = [s for s in symbols_to_add if s not in self.initializing_symbol_prices_pairs]
        if new_symbols_to_add:
            self.logger.debug(f"Fetching price for {new_symbols_to_add} to compute all the "
                              f"currencies values and properly evaluate portfolio.")
            self._ask_ticker_data_for_currency(new_symbols_to_add)
            self.initializing_symbol_prices.add(currency)
            self.initializing_symbol_prices_pairs.update(new_symbols_to_add)

    def _ask_ticker_data_for_currency(self, symbols_to_add):
        """
        Synchronously call TICKER_CHANNEL producer to add a list of new symbols to its watch list
        :param symbols_to_add: the list of symbol to add to the TICKER_CHANNEL producer watch list
        """
        asyncio.run_coroutine_threadsafe(
            self.portfolio_manager.exchange_manager.exchange_config.add_watched_symbols(symbols_to_add),
            asyncio.get_running_loop())

    def _inform_no_matching_symbol(self, currency):
        """
        Log a missing currency pair to calculate the portfolio profitability
        :param currency: the concerned currency
        """
        # do not log warning in backtesting or tests
        if not self.portfolio_manager.exchange_manager.is_backtesting:
            self.logger.warning(f"No trading pair including {currency} and {self.portfolio_manager.reference_market} on"
                                f" {self.portfolio_manager.exchange_manager.exchange_name}. {currency} "
                                f"can't be valued for portfolio and profitability.")

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
        TODO do not use config[CONFIG_CRYPTO_CURRENCIES]
        :param evaluated_pair_values: the list of evaluated pairs
        :param evaluated_currencies: the list of evaluated currencies
        :param missing_tickers: the list of missing currencies
        """
        if self.portfolio_manager.exchange_manager.exchange_config.all_config_symbol_pairs:
            currency, market = symbol_util.parse_symbol(
                self.portfolio_manager.exchange_manager.exchange_config.all_config_symbol_pairs[0]
            ).base_and_quote()
            currency_to_evaluate = currency
            try:
                if currency not in evaluated_currencies:
                    evaluated_pair_values[currency] = self._evaluate_value(currency, constants.ONE)
                    evaluated_currencies.add(currency)
                if market not in evaluated_currencies:
                    currency_to_evaluate = market
                    evaluated_pair_values[market] = self._evaluate_value(market, constants.ONE)
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
                        currency, portfolio, ignore_missing_currency_data):
                    evaluated_pair_values[currency] = self._evaluate_value(currency, constants.ONE)
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
            if currency not in self.missing_currency_data_in_exchange
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
            return self._evaluate_value(currency, portfolio[currency].total, raise_error)
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
        return (currency not in self.missing_currency_data_in_exchange or ignore_missing_currency_data) and \
               (portfolio[currency].total > constants.ZERO or currency in
                self.portfolio_manager.portfolio_profitability.valuated_currencies)
