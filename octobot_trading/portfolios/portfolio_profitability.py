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

from octobot_commons.constants import CONFIG_CRYPTO_CURRENCIES
from octobot_commons.logging.logging_util import get_logger
from octobot_commons.symbol_util import split_symbol

from octobot_trading.util import get_all_currencies


class PortfolioProfitability:
    """
    PortfolioProfitability calculates the portfolio profitability
    by subtracting portfolio_current_value and portfolio_origin_value
    """

    def __init__(self, portfolio_manager):
        self.portfolio_manager = portfolio_manager
        self.value_manager = portfolio_manager.portfolio_value_manager
        self.logger = get_logger(f"{self.__class__.__name__}[{self.portfolio_manager.exchange_manager.exchange_name}]")

        # profitability attributes
        self.profitability = 0
        self.profitability_percent = 0
        self.profitability_diff = 0
        self.market_profitability_percent = 0
        self.initial_portfolio_current_profitability = 0

        # buffer of currencies excluding market only used currencies ex: conf = btc/usd, eth/btc, ltc/btc, here usd
        # is market only => not used to compute market average profitability
        self.traded_currencies_without_market_specific = set()

        # set of currencies that should be traded because either present in config or as a reference market
        self.traded_currencies = get_all_currencies(self.portfolio_manager.config)
        self.traded_currencies.add(self.portfolio_manager.reference_market)

    def get_average_market_profitability(self):
        """
        Returns the % move average of all the watched cryptocurrencies between bot's start time and now
        :return: the average market profitability
        """
        self.portfolio_manager.portfolio_value_manager.get_current_crypto_currencies_values()
        return self._calculate_average_market_profitability()

    async def update_profitability(self, force_recompute_origin_portfolio=False) -> bool:
        """
        Get profitability calls get_currencies_prices to update required data
        Then calls get_portfolio_current_value to set the current value of portfolio_current_value attribute
        :return: True if changed else False
        """
        self._reset_before_profitability_calculation()
        try:
            await self.portfolio_manager.handle_profitability_recalculation(force_recompute_origin_portfolio)
            self._update_profitability_calculation()
            return self.profitability_diff != 0
        except KeyError as missing_data_exception:
            self.logger.warning(f"Missing ticker data to calculate profitability")
            self.logger.warning(f"Missing {missing_data_exception} ticker data to calculate profitability")
        except Exception as missing_data_exception:
            self.logger.exception(missing_data_exception, True, str(missing_data_exception))

    def _reset_before_profitability_calculation(self):
        """
        Prepare profitability calculation
        """
        self.profitability_diff = self.profitability_percent
        self.profitability = 0
        self.profitability_percent = 0
        self.market_profitability_percent = 0
        self.initial_portfolio_current_profitability = 0

    def _update_profitability_calculation(self):
        """
        Calculates the new portfolio profitability
        """
        initial_portfolio_current_value = self.value_manager.get_origin_portfolio_current_value()
        self.profitability = self.value_manager.portfolio_current_value - self.value_manager.portfolio_origin_value

        if self.value_manager.portfolio_origin_value > 0:
            self.profitability_percent = (100 * self.value_manager.portfolio_current_value /
                                          self.value_manager.portfolio_origin_value) - 100
            self.initial_portfolio_current_profitability = \
                (100 * initial_portfolio_current_value / self.value_manager.portfolio_origin_value) - 100
        else:
            self.profitability_percent = 0
        self._update_portfolio_delta()

    def _update_portfolio_delta(self):
        """
        Calculates difference between the current and the last portfolio
        """
        self.profitability_diff = self.profitability_percent - self.profitability_diff
        self.market_profitability_percent = self.get_average_market_profitability()

    def _calculate_average_market_profitability(self):
        """
        Calculate the average of all the watched cryptocurrencies between bot's start time and now
        :return: the calculation result
        """
        origin_values = [value / self.value_manager.origin_crypto_currencies_values[currency]
                         for currency, value
                         in self._only_symbol_currency_filter(self.value_manager.
                                                              current_crypto_currencies_values).items()
                         if self.value_manager.origin_crypto_currencies_values[currency] > 0]

        return sum(origin_values) / len(origin_values) * 100 - 100 if origin_values else 0

    def _only_symbol_currency_filter(self, currency_dict):
        """
        Return the dict of traded currencies with their portfolio value
        :param currency_dict: the currency dictionary to be filtered
        :return: the currency portfolio value filtered
        """
        if not self.traded_currencies_without_market_specific:
            self._init_traded_currencies_without_market_specific()
        return {currency: v for currency, v in currency_dict.items()
                if currency in self.traded_currencies_without_market_specific}

    def _init_traded_currencies_without_market_specific(self):
        """
        Initialize traded currencies without market specific set
        TODO do not use config[CONFIG_CRYPTO_CURRENCIES]
        """
        self.traded_currencies_without_market_specific = set(
            split_symbol(pair)[0]
            for cryptocurrency in self.portfolio_manager.config[CONFIG_CRYPTO_CURRENCIES]
            for pair in self.portfolio_manager.exchange_manager.exchange_config.get_traded_pairs(cryptocurrency)
        )
