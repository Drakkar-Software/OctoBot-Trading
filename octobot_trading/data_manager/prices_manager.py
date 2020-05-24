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
from asyncio import Event, wait_for

from octobot_commons.constants import MINUTE_TO_SECONDS
from octobot_commons.logging.logging_util import get_logger
from octobot_trading.util.initializable import Initializable


class PricesManager(Initializable):
    MARK_PRICE_VALIDITY = 5 * MINUTE_TO_SECONDS

    def __init__(self, exchange_manager, price_events_manager):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.mark_price = 0
        self.mark_price_set_time = 0
        self.exchange_manager = exchange_manager
        self.price_events_manager = price_events_manager

        # warning: should only be created in the async loop thread
        self.valid_price_received_event = Event()

    async def initialize_impl(self):
        self._reset_prices()

    def set_mark_price(self, mark_price):
        self.mark_price = mark_price
        self.mark_price_set_time = self.exchange_manager.exchange.get_exchange_current_time()
        self.price_events_manager.handle_price(self.mark_price, self.mark_price_set_time)
        self.valid_price_received_event.set()

    async def get_mark_price(self, timeout=MARK_PRICE_VALIDITY):
        self._ensure_price_validity()
        if not self.valid_price_received_event.is_set():
            await wait_for(self.valid_price_received_event.wait(), timeout)
        return self.mark_price

    def _ensure_price_validity(self):
        if self.exchange_manager.exchange.get_exchange_current_time() - self.mark_price_set_time > \
          self.MARK_PRICE_VALIDITY:
            self.valid_price_received_event.clear()

    def _reset_prices(self):
        self.mark_price = 0
        self.mark_price_set_time = 0
        self.valid_price_received_event.clear()


def calculate_mark_price_from_recent_trade_prices(recent_trade_prices):
    return sum(recent_trade_prices) / len(recent_trade_prices) if recent_trade_prices else 0
