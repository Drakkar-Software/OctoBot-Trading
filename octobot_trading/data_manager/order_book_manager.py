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
from octobot_commons.logging.logging_util import get_logger

from octobot_trading.util.initializable import Initializable


class OrderBookManager(Initializable):
    def __init__(self):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.order_book_initialized = False
        self.bids = []
        self.asks = []
        self.ask_quantity, self.ask_price, self.bid_quantity, self.bid_price = 0, 0, 0, 0

    async def initialize_impl(self):
        self.reset_order_book()

    def reset_order_book(self):
        self.order_book_initialized = False
        self.bids = []
        self.asks = []
        self.ask_quantity, self.ask_price, self.bid_quantity, self.bid_price = 0, 0, 0, 0

    def order_book_update(self, asks, bids):
        self.order_book_initialized = True
        if asks:
            self.asks = asks
        if bids:
            self.bids = bids

    def order_book_ticker_update(self, ask_quantity, ask_price, bid_quantity, bid_price):
        self.ask_quantity, self.ask_price = ask_quantity, ask_price
        self.bid_quantity, self.bid_price = bid_quantity, bid_price
