# pylint: disable=E0611
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

from octobot_trading.channels.exchange_channel import get_chan
from octobot_trading.constants import ORDER_BOOK_CHANNEL, ORDER_BOOK_TICKER_CHANNEL
from octobot_trading.channels.order_book import OrderBookProducer
from octobot_trading.enums import ExchangeConstantsOrderBookInfoColumns, RestExchangePairsRefreshMaxThresholds


class OrderBookUpdater(OrderBookProducer):
    CHANNEL_NAME = ORDER_BOOK_CHANNEL
    ORDER_BOOK_REFRESH_TIME = 5

    def __init__(self, channel):
        super().__init__(channel)
        self.refresh_time = OrderBookUpdater.ORDER_BOOK_REFRESH_TIME

    async def start(self):
        refresh_threshold = self.channel.exchange_manager.get_rest_pairs_refresh_threshold()
        if refresh_threshold is RestExchangePairsRefreshMaxThresholds.MEDIUM:
            self.refresh_time = 9
        elif refresh_threshold is RestExchangePairsRefreshMaxThresholds.SLOW:
            self.refresh_time = 15
        if self.channel.is_paused:
            await self.pause()
        else:
            await self.start_update_loop()

    async def start_update_loop(self):
        while not self.should_stop and not self.channel.is_paused:
            try:
                for pair in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
                    order_book = await self.channel.exchange_manager.exchange.get_order_book(pair)
                    try:
                        asks, bids = order_book[ExchangeConstantsOrderBookInfoColumns.ASKS.value], \
                                     order_book[ExchangeConstantsOrderBookInfoColumns.BIDS.value]

                        await self.parse_order_book_ticker(pair, asks, bids)
                        await self.push(pair, asks, bids)
                    except TypeError as e:
                        self.logger.error(f"Failed to fetch order book for {pair} : {e}")
                await asyncio.sleep(self.refresh_time)
            except NotSupported:
                self.logger.warning(f"{self.channel.exchange_manager.exchange_name} is not supporting updates")
                await self.pause()
            except Exception as e:
                self.logger.exception(e, True, f"Fail to update order book : {e}")

    async def parse_order_book_ticker(self, pair, asks, bids):
        """
        Order book ticker
        """
        try:
            if asks and bids:
                await get_chan(ORDER_BOOK_TICKER_CHANNEL, self.channel.exchange_manager.id).get_internal_producer(). \
                    push(symbol=pair,
                         ask_quantity=asks[0][1], ask_price=asks[0][0],
                         bid_quantity=bids[0][1], bid_price=bids[0][0])
        except Exception as e:
            self.logger.error(f"Failed to parse order book ticker : {e}")

    async def resume(self) -> None:
        await super().resume()
        if not self.is_running:
            await self.run()
