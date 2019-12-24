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

from octobot_commons.logging.logging_util import get_logger
from octobot_trading.util.initializable import Initializable


class PricesManager(Initializable):
    MARK_PRICE_TIMEOUT = 60

    def __init__(self):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.mark_price = 0
        self.prices_initialized_event = Event()

    async def initialize_impl(self):
        self.__reset_prices()

    def set_mark_price(self, mark_price):
        self.mark_price = mark_price
        self.prices_initialized_event.set()

    async def get_mark_price(self, timeout=MARK_PRICE_TIMEOUT):
        await wait_for(self.prices_initialized_event.wait(), timeout)
        return self.mark_price

    def __reset_prices(self):
        self.mark_price = 0

    @staticmethod
    def calculate_mark_price_from_recent_trade_prices(recent_trade_prices):
        return sum(recent_trade_prices) / len(recent_trade_prices)
