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

from octobot_trading.channels.order_book import OrderBookProducer
from octobot_trading.enums import ExchangeConstantsOrderBookInfoColumns


class OrderBookUpdater(OrderBookProducer):
    ORDER_BOOK_REFRESH_TIME = 60

    def __init__(self, channel):
        super().__init__(channel)
        self.should_stop = False
        self.channel = channel

    async def start(self):
        while not self.should_stop:
            try:
                for pair in self.channel.exchange_manager.traded_pairs:
                    order_book = await self.channel.exchange_manager.exchange.get_order_book(pair)
                    asks, bids = order_book[ExchangeConstantsOrderBookInfoColumns.ASKS.value], \
                                 order_book[ExchangeConstantsOrderBookInfoColumns.BIDS.value]
                    await self.perform(pair, asks, bids)
                    await self.push(pair, asks, bids)
                await asyncio.sleep(self.ORDER_BOOK_REFRESH_TIME)
            except Exception as e:
                self.logger.exception(f"Fail to update : {e}")
