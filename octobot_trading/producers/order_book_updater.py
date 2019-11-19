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

from ccxt.base.errors import NotSupported

from octobot_trading.constants import ORDER_BOOK_CHANNEL
from octobot_trading.channels.order_book import OrderBookProducer
from octobot_trading.enums import ExchangeConstantsOrderBookInfoColumns


class OrderBookUpdater(OrderBookProducer):
    CHANNEL_NAME = ORDER_BOOK_CHANNEL
    ORDER_BOOK_REFRESH_TIME = 5

    async def start(self):
        while not self.should_stop and not self.channel.is_paused:
            try:
                for pair in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
                    order_book = await self.channel.exchange_manager.exchange.get_order_book(pair)
                    try:
                        asks, bids = order_book[ExchangeConstantsOrderBookInfoColumns.ASKS.value], \
                                     order_book[ExchangeConstantsOrderBookInfoColumns.BIDS.value]
                        await self.push(pair, asks, bids)
                    except TypeError:
                        pass
                await asyncio.sleep(self.ORDER_BOOK_REFRESH_TIME)
            except NotSupported:
                self.logger.warning(f"{self.channel.exchange_manager.exchange.name} is not supporting updates")
                await self.pause()
            except Exception as e:
                self.logger.exception(f"Fail to update order book : {e}")

    async def resume(self) -> None:
        await super().resume()
        if not self.is_running:
            await self.run()
