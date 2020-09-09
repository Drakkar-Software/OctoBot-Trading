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
from octobot_commons.constants import PORTFOLIO_TOTAL, CONFIG_CRYPTO_CURRENCIES
from octobot_commons.logging.logging_util import get_logger
from octobot_commons.symbol_util import split_symbol, merge_currencies

from octobot_trading.constants import TICKER_CHANNEL
from octobot_trading.channels.exchange_channel import get_chan
from octobot_trading.constants import CONFIG_PORTFOLIO_TOTAL
from octobot_trading.util import get_reference_market, get_all_currencies


class PortfolioProfitabilty:
    """
    PortfolioProfitabilty calculates the portfolio profitability
    by subtracting portfolio_current_value and portfolio_origin_value
    """

    def __init__(self, config, trader, portfolio_manager, exchange_manager):
        super().__init__()
        self.config = config
        self.trader = trader
        self.portfolio_manager = portfolio_manager
        self.exchange_manager = exchange_manager
        self.logger = get_logger(f"{self.__class__.__name__}[{self.exchange_manager.exchange_name}]")

        self.profitability = 0
        self.profitability_percent = 0
        self.profitability_diff = 0
        self.market_profitability_percent = 0
        self.initial_portfolio_current_profitability = 0
        self.initializing_symbol_prices = set()

        self.reference_market = get_reference_market(self.config)

        self.portfolio_origin_value = 0
        self.portfolio_current_value = 0

        self.currencies_last_prices = {}
        self.origin_crypto_currencies_values = {}
        self.current_crypto_currencies_values = {}
        self.origin_portfolio = None

        # buffer of currencies excluding market only used currencies ex: conf = btc/usd, eth/btc, ltc/btc, here usd
        # is market only => not used to compute market average profitability
        self.traded_currencies_without_market_specific = set()

        # set of currencies that should be traded because either present in config or as a reference market
        self.traded_currencies = get_all_currencies(self.config)
        self.traded_currencies.add(self.reference_market)

        # set of currencies for which the current exchange is not providing any suitable price data
        self.missing_currency_data_in_exchange = set()

    async def handle_mark_price_update(self, symbol, mark_price):
        """
        Handle a mark price update notification
        :param symbol: the update symbol
        :param mark_price: the updated mark price
        :return: True if profitability changed
        """
        force_recompute_origin_portfolio = False
        currency, market = split_symbol(symbol)
        if currency not in set(self.origin_crypto_currencies_values.keys()) and market == self.reference_market:
            # will fail if symbol doesn't have a price in self.origin_crypto_currencies_values and therefore
            # requires the origin portfolio value to be recomputed using this price info in case this price is relevant
            force_recompute_origin_portfolio = True
            self.origin_crypto_currencies_values[currency] = mark_price
        self.currencies_last_prices[symbol] = mark_price
        return await self._update_profitability(force_recompute_origin_portfolio)

    async def handle_balance_update(self, balance):
        """
        Handle balance update notification
        :param balance: the updated balance
        :return: True if profitability changed
        """
        return await self._update_profitability()

    async def _update_profitability(self, force_recompute_origin_portfolio=False):
        """
        Get profitability calls get_currencies_prices to update required data
        Then calls get_portfolio_current_value to set the current value of portfolio_current_value attribute
        Returns True if changed else False
        """
        self.profitability_diff = self.profitability_percent
        self.profitability = 0
        self.profitability_percent = 0
        self.market_profitability_percent = 0
        self.initial_portfolio_current_profitability = 0

        try:
            await self._update_portfolio_and_currencies_current_value()

            if self.portfolio_origin_value == 0:
                # try to update portfolio origin value if it's not known yet
                await self._init_origin_portfolio_and_currencies_value()
            if force_recompute_origin_portfolio:
                await self._recompute_origin_portfolio_initial_value()

            initial_portfolio_current_value = await self._get_origin_portfolio_current_value()

            self.profitability = self.portfolio_current_value - self.portfolio_origin_value

            if self.portfolio_origin_value > 0:
                self.profitability_percent = (100 * self.portfolio_current_value / self.portfolio_origin_value) - 100
                self.initial_portfolio_current_profitability = \
                    (100 * initial_portfolio_current_value / self.portfolio_origin_value) - 100
            else:
                self.profitability_percent = 0

            # calculate difference with the last current portfolio
            self.profitability_diff = self.profitability_percent - self.profitability_diff

            self.market_profitability_percent = await self.get_average_market_profitability()

            return self.profitability_diff != 0
        except KeyError as e:
            self.logger.warning(f"Missing ticker data to calculate profitability")
            self.logger.warning(f"Missing {e} ticker data to calculate profitability")
        except Exception as e:
            self.logger.exception(e, True, str(e))

    async def get_average_market_profitability(self):
        """
        Returns the % move average of all the watched cryptocurrencies between bot's start time and now
        :return: the average market profitability
        """
        await self.get_current_crypto_currencies_values()

        origin_values = [value / self.origin_crypto_currencies_values[currency]
                         for currency, value
                         in self._only_symbol_currency_filter(self.current_crypto_currencies_values).items()
                         if self.origin_crypto_currencies_values[currency] > 0]

        return sum(origin_values) / len(origin_values) * 100 - 100 if origin_values else 0

    async def get_current_crypto_currencies_values(self):
        """
        Return the current crypto-currencies values
        :return: the current crypto-currencies values
        """
        if not self.current_crypto_currencies_values:
            await self._update_portfolio_and_currencies_current_value()
        return self.current_crypto_currencies_values

    async def get_current_holdings_values(self):
        """
        Get holdings ratio for each currencies
        :return: the holdings ratio dictionary
        """
        holdings = await self.get_current_crypto_currencies_values()
        return {currency: await self._get_currency_value(self.portfolio_manager.portfolio.portfolio, currency, holdings)
                for currency in holdings.keys()}

    async def holdings_ratio(self, currency):
        """
        Return the holdings ratio for the specified currency
        :param currency: the currency
        :return: the holdings ratio
        """
        currency_holdings: float = self.portfolio_manager.portfolio.get_currency_from_given_portfolio(currency,
                                                                                                      PORTFOLIO_TOTAL)
        currency_value: float = await self._evaluate_value(currency, currency_holdings)
        return currency_value / self.portfolio_current_value if self.portfolio_current_value else 0

    async def update_portfolio_current_value(self, portfolio, currencies_values=None, fill_currencies_values=False):
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
                await self._evaluate_config_crypto_currencies_and_portfolio_values(portfolio))
            if fill_currencies_values:
                for currency, value in self.current_crypto_currencies_values.items():
                    if currency not in currencies_values:
                        currencies_values[currency] = value
            values = self.current_crypto_currencies_values
        return await self._evaluate_portfolio_value(portfolio, values)

    def _only_symbol_currency_filter(self, currency_dict):
        if not self.traded_currencies_without_market_specific:
            self._init_traded_currencies_without_market_specific()
        return {currency: v for currency, v in currency_dict.items()
                if currency in self.traded_currencies_without_market_specific}

    def _init_traded_currencies_without_market_specific(self):
        for cryptocurrency in self.config[CONFIG_CRYPTO_CURRENCIES]:
            for pair in self.exchange_manager.exchange_config.get_traded_pairs(cryptocurrency):
                symbol, _ = split_symbol(pair)
                if symbol not in self.traded_currencies_without_market_specific:
                    self.traded_currencies_without_market_specific.add(symbol)

    async def _evaluate_value(self, currency, quantity, raise_error=True):
        """
        Evaluate value returns the currency quantity value in the reference (attribute) currency
        :param currency: the currency to evaluate
        :param quantity: the currency quantity
        :param raise_error: will catch exception if False
        :return: the currency value
        """
        # easy case --> the current currency is the reference currency or the quantity is 0
        if currency == self.reference_market or quantity == 0:
            return quantity
        currency_value = await self._try_get_value_of_currency(currency, quantity, raise_error)
        if currency_value > 0 and currency in self.initializing_symbol_prices:
            self.initializing_symbol_prices.remove(currency)
        return currency_value

    async def _update_portfolio_and_currencies_current_value(self):
        """
        Update the portfolio current value with the current portfolio instance
        """
        self.portfolio_current_value = await self.update_portfolio_current_value(
            self.portfolio_manager.portfolio.portfolio)

    async def _init_origin_portfolio_and_currencies_value(self):
        self.origin_portfolio = self.origin_portfolio or await self.portfolio_manager.portfolio.copy()
        self.origin_crypto_currencies_values.update(
            await self._evaluate_config_crypto_currencies_and_portfolio_values(self.origin_portfolio.portfolio,
                                                                               ignore_missing_currency_data=True))
        await self._recompute_origin_portfolio_initial_value()

    async def _recompute_origin_portfolio_initial_value(self):
        self.portfolio_origin_value = \
            await self.update_portfolio_current_value(self.origin_portfolio.portfolio,
                                                      currencies_values=self.origin_crypto_currencies_values,
                                                      fill_currencies_values=True)

    async def _get_origin_portfolio_current_value(self, refresh_values=False):
        if refresh_values:
            self.current_crypto_currencies_values.update(
                await self._evaluate_config_crypto_currencies_and_portfolio_values(self.origin_portfolio.portfolio))
        return await self.update_portfolio_current_value(self.origin_portfolio.portfolio,
                                                         currencies_values=self.current_crypto_currencies_values)

    async def _try_get_value_of_currency(self, currency, quantity, raise_error):
        """ try_get_value_of_currency will try to obtain the current value of the currency quantity
        in the reference currency.
        It will try to create the symbol that fit with the exchange logic.
        Returns the value found of this currency quantity, if not found returns 0.
        """
        symbol = merge_currencies(currency, self.reference_market)
        symbol_inverted = merge_currencies(self.reference_market, currency)

        try:
            if self.exchange_manager.symbol_exists(symbol):
                return self.currencies_last_prices[symbol] * quantity

            elif self.exchange_manager.symbol_exists(symbol_inverted) and \
                    self.currencies_last_prices[symbol_inverted] != 0:
                return quantity / self.currencies_last_prices[symbol_inverted]
            if currency not in self.missing_currency_data_in_exchange:
                self._inform_no_matching_symbol(currency)
                self.missing_currency_data_in_exchange.add(currency)
            return 0
        except KeyError as e:
            if not self.exchange_manager.is_backtesting:
                symbols_to_add = []
                if self.exchange_manager.symbol_exists(symbol):
                    symbols_to_add = [symbol]
                elif self.exchange_manager.symbol_exists(symbol_inverted):
                    symbols_to_add = [symbol_inverted]

                if symbols_to_add:
                    await get_chan(TICKER_CHANNEL, self.exchange_manager.id).modify(added_pairs=symbols_to_add)
                    self.initializing_symbol_prices.add(currency)
                if raise_error:
                    raise e
            return 0

    def _inform_no_matching_symbol(self, currency):
        # do not log warning in backtesting or tests
        if not self.exchange_manager.is_backtesting:
            self.logger.warning(f"No trading pair including {currency} and {self.reference_market} on "
                                f"{self.exchange_manager.exchange_name}. {currency} can't be valued for portfolio and "
                                f"profitability.")

    async def _evaluate_config_crypto_currencies_and_portfolio_values(self,
                                                                      portfolio,
                                                                      ignore_missing_currency_data=False):
        values_dict = {}
        evaluated_currencies = set()
        missing_tickers = set()
        # evaluate config currencies
        for cryptocurrency in self.config[CONFIG_CRYPTO_CURRENCIES]:
            pairs = self.exchange_manager.exchange_config.get_traded_pairs(cryptocurrency)
            if pairs:
                currency, market = split_symbol(pairs[0])
                currency_to_evaluate = currency
                try:
                    if currency not in evaluated_currencies:
                        values_dict[currency] = await self._evaluate_value(currency, 1)
                        evaluated_currencies.add(currency)
                    if market not in evaluated_currencies:
                        currency_to_evaluate = market
                        values_dict[market] = await self._evaluate_value(market, 1)
                        evaluated_currencies.add(market)
                except KeyError:
                    missing_tickers.add(currency_to_evaluate)
        # evaluate portfolio currencies
        for currency in portfolio:
            try:
                if currency not in evaluated_currencies and self._should_currency_be_considered(
                        currency, portfolio, ignore_missing_currency_data):
                    values_dict[currency] = await self._evaluate_value(currency, 1)
                    evaluated_currencies.add(currency)
            except KeyError:
                missing_tickers.add(currency)
        if missing_tickers:
            self.logger.debug(f"Missing price data for {missing_tickers}, impossible to compute all the "
                              f"currencies values for now.")
        return values_dict

    async def _evaluate_portfolio_value(self, portfolio, currencies_values=None):
        """
        Perform evaluate_value with a portfolio configuration
        :param portfolio: the portfolio to explore
        :param currencies_values: currencies to evaluate
        :return: the calculated quantity value in reference (attribute) currency
        """
        return sum([
            await self._get_currency_value(portfolio, currency, currencies_values)
            for currency in portfolio
            if currency not in self.missing_currency_data_in_exchange
        ])

    async def _get_currency_value(self, portfolio, currency, currencies_values=None, raise_error=False):
        if currency in portfolio and portfolio[currency][CONFIG_PORTFOLIO_TOTAL] != 0:
            if currencies_values and currency in currencies_values:
                return currencies_values[currency] * portfolio[currency][CONFIG_PORTFOLIO_TOTAL]
            else:
                return await self._evaluate_value(currency, portfolio[currency][CONFIG_PORTFOLIO_TOTAL], raise_error)
        return 0

    def _should_currency_be_considered(self, currency, portfolio, ignore_missing_currency_data):
        return (currency not in self.missing_currency_data_in_exchange or ignore_missing_currency_data) and \
               (portfolio[currency][PORTFOLIO_TOTAL] > 0 or currency in self.traded_currencies)
