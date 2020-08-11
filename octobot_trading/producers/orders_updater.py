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

from octobot_trading.channels.orders import OrdersProducer
from octobot_trading.constants import ORDERS_CHANNEL


class OpenOrdersUpdater(OrdersProducer):
    CHANNEL_NAME = ORDERS_CHANNEL
    ORDERS_STARTING_REFRESH_TIME = 10
    ORDERS_REFRESH_TIME = 14
    ORDERS_UPDATE_LIMIT = 200
    SHOULD_CHECK_MISSING_OPEN_ORDERS = True

    async def initialize(self):
        try:
            await self.fetch_and_push()
        except Exception as e:
            self.logger.error(f"Fail to initialize open orders : {e}")

    async def start(self):
        await self.initialize()
        await asyncio.sleep(self.ORDERS_STARTING_REFRESH_TIME)
        while not self.should_stop:
            try:
                await self.fetch_and_push(is_from_bot=True, limit=self.ORDERS_UPDATE_LIMIT)
            except NotSupported:
                self.logger.warning(f"{self.channel.exchange_manager.exchange_name} is not supporting updates")
                await self.pause()
            except Exception as e:
                self.logger.error(f"Fail to update open orders : {e}")

            await asyncio.sleep(self.ORDERS_REFRESH_TIME)

    async def fetch_and_push(self, is_from_bot=False, limit=None):
        for symbol in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
            open_orders: list = await self.channel.exchange_manager.exchange.get_open_orders(symbol=symbol, limit=limit)
            if open_orders:
                await self.push(orders=list(map(self.channel.exchange_manager.exchange.clean_order, open_orders)),
                                is_from_bot=is_from_bot)

    async def resume(self) -> None:
        await super().resume()
        if not self.is_running:
            await self.run()


class CloseOrdersUpdater(OrdersProducer):
    CHANNEL_NAME = ORDERS_CHANNEL
    ORDERS_REFRESH_TIME = 32
    ORDERS_UPDATE_LIMIT = 200

    async def start(self):
        while not self.should_stop:
            try:
                await self.fetch_and_push()
            except NotSupported:
                self.logger.warning(f"{self.channel.exchange_manager.exchange_name} is not supporting updates")
                await self.pause()
            except Exception as e:
                self.logger.error(f"Fail to update closed orders : {e}")

            await asyncio.sleep(self.ORDERS_REFRESH_TIME)

    async def fetch_and_push(self):
        for symbol in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
            close_orders: list = await self.channel.exchange_manager.exchange.get_closed_orders(
                symbol=symbol,
                limit=self.ORDERS_UPDATE_LIMIT)

            if close_orders:
                await self.push(orders=list(map(self.channel.exchange_manager.exchange.clean_order, close_orders)),
                                are_closed=True)

    async def resume(self) -> None:
        await super().resume()
        if not self.is_running:
            await self.run()
