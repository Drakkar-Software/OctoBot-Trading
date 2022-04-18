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
import decimal

import octobot_commons.constants as commons_constants
import octobot_commons.logging as logging

import octobot_trading.enums as enums
import octobot_trading.util as util
import octobot_trading.constants as constants


class PricesManager(util.Initializable):
    MARK_PRICE_FETCH_TIMEOUT = 5 * commons_constants.MINUTE_TO_SECONDS

    def __init__(self, exchange_manager):
        super().__init__()
        self.mark_price = constants.ZERO
        self.mark_price_set_time = 0
        self.mark_price_from_sources = {}
        self.exchange_manager = exchange_manager
        self.logger = logging.get_logger(f"{self.__class__.__name__}[{self.exchange_manager.exchange_name}]")
        self.price_validity = self._compute_mark_price_validity_timeout()

        # warning: should only be created in the async loop thread
        self.valid_price_received_event = asyncio.Event()

    async def initialize_impl(self):
        """
        Initialize PricesManager attributes with default
        """
        self._reset_prices()

    def set_mark_price(self, mark_price, mark_price_source) -> bool:
        """
        Set the mark price if the mark price come from MarkPriceSources.EXCHANGE_MARK_PRICE
        Set the mark price if the mark price come from MarkPriceSources.RECENT_TRADE_AVERAGE and
        if it's not the first update for MarkPriceSources.RECENT_TRADE_AVERAGE
        Set the mark price if the mark price come from MarkPriceSources.TICKER_CLOSE_PRICE and
        if other sources have expired
        :param mark_price: the mark price value from mark_price_source in float
        :param mark_price_source: the mark_price source (from MarkPriceSources)
        :return True if mark price got updated
        """
        is_mark_price_updated = False
        if mark_price_source == enums.MarkPriceSources.EXCHANGE_MARK_PRICE.value:
            self._set_mark_price_value(mark_price)
            is_mark_price_updated = True

        # set mark price value if MarkPriceSources.RECENT_TRADE_AVERAGE.value has already been updated
        elif mark_price_source == enums.MarkPriceSources.RECENT_TRADE_AVERAGE.value:
            if self.mark_price_from_sources.get(enums.MarkPriceSources.RECENT_TRADE_AVERAGE.value, None) is not None:
                self._set_mark_price_value(mark_price)
                is_mark_price_updated = True
            else:
                # set time at 0 to ensure invalid price but keep track of initialization
                self.mark_price_from_sources[mark_price_source] = (mark_price, 0)

        # set mark price value if other sources have expired
        elif mark_price_source == enums.MarkPriceSources.TICKER_CLOSE_PRICE.value and not \
                self._are_other_sources_valid(enums.MarkPriceSources.TICKER_CLOSE_PRICE.value):
            self._set_mark_price_value(mark_price)
            is_mark_price_updated = True

        if is_mark_price_updated:
            self.mark_price_from_sources[mark_price_source] = \
                (mark_price, self.exchange_manager.exchange.get_exchange_current_time())
        return is_mark_price_updated

    async def get_mark_price(self, timeout=MARK_PRICE_FETCH_TIMEOUT):
        """
        Return mark price if valid
        :param timeout: event wait timeout
        :return: the mark price if valid
        """
        self._ensure_price_validity()
        if not self.valid_price_received_event.is_set():
            try:
                self.exchange_manager.ensure_reachability()
                if self.exchange_manager.is_backtesting:
                    # should never happen in backtesting: mark price is either available
                    # or exchange should be unreachable
                    raise asyncio.TimeoutError()
                await asyncio.wait_for(self.valid_price_received_event.wait(), timeout)
            except asyncio.TimeoutError:
                self.logger.warning("Timeout when waiting for current market price. This probably means that too many "
                                    "trading pairs are being used at the same time and the exchange's rate limit is "
                                    "preventing OctoBot from working properly. If this issue persists, please consider "
                                    "using websocket connections.")
                raise
        return self.mark_price

    def _set_mark_price_value(self, mark_price):
        """
        Called when a new mark price value has been calculated or provided by the exchange
        """
        self.mark_price = mark_price
        self.mark_price_set_time = self.exchange_manager.exchange.get_exchange_current_time()
        self.valid_price_received_event.set()

    def _are_other_sources_valid(self, mark_price_source):
        """
        Check if other sources a out of validity
        """
        for source in enums.MarkPriceSources:
            source_mark_price = self.mark_price_from_sources.get(source.value, None)
            if source_mark_price is not None and \
                    mark_price_source != source.value and \
                    self._is_mark_price_valid(source_mark_price[1]):
                return True
        return False

    def _ensure_price_validity(self):
        """
        Clear the event price validity event if the mark price has expired
        """
        if not self._is_mark_price_valid(self.mark_price_set_time):
            self.valid_price_received_event.clear()

    def _compute_mark_price_validity_timeout(self):
        refresh_threshold = self.exchange_manager.get_rest_pairs_refresh_threshold()
        if refresh_threshold is enums.RestExchangePairsRefreshMaxThresholds.FAST:
            return 3 * commons_constants.MINUTE_TO_SECONDS
        if refresh_threshold is enums.RestExchangePairsRefreshMaxThresholds.MEDIUM:
            return 5 * commons_constants.MINUTE_TO_SECONDS
        return 7 * commons_constants.MINUTE_TO_SECONDS

    def _is_mark_price_valid(self, mark_price_updated_time):
        """
        Check if a mark price value has expired
        :param mark_price_updated_time: the mark price updated time
        :return: True if the difference between mark_price_updated_time and now is < self.price_validity
        """
        return self.exchange_manager.exchange.get_exchange_current_time() - mark_price_updated_time < \
            self.price_validity

    def _reset_prices(self):
        """
        Reset PricesManager attributes values
        """
        self.mark_price = constants.ZERO
        self.mark_price_set_time = 0
        self.valid_price_received_event.clear()
        self.mark_price_from_sources = {}


def calculate_mark_price_from_recent_trade_prices(recent_trade_prices):
    return decimal.Decimal(sum(recent_trade_prices)) / decimal.Decimal(len(recent_trade_prices)) \
        if recent_trade_prices else constants.ZERO
