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
    ORDERS_REFRESH_TIME = 12
    ORDERS_UPDATE_LIMIT = 10

    async def initialize(self):
        try:
            for symbol in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
                open_orders: list = await self.channel.exchange_manager.exchange.get_open_orders(symbol=symbol)

                if open_orders:
                    await self.push(orders=list(map(self.channel.exchange_manager.exchange.clean_trade, open_orders)),
                                    is_from_bot=False)

                await asyncio.sleep(self.ORDERS_STARTING_REFRESH_TIME)
        except Exception as e:
            self.logger.error(f"Fail to initialize open orders : {e}")

    async def start(self):
        await self.initialize()
        while not self.should_stop and not self.channel.is_paused:
            try:
                for symbol in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
                    open_orders: list = await self.channel.exchange_manager.exchange.get_open_orders(
                        symbol=symbol,
                        limit=self.ORDERS_UPDATE_LIMIT)

                    if open_orders:
                        await self.push(orders=list(map(self.channel.exchange_manager.exchange.clean_order,
                                                        open_orders)))
            except NotSupported:
                self.logger.warning(f"{self.channel.exchange_manager.exchange_name} is not supporting updates")
                await self.pause()
            except Exception as e:
                self.logger.error(f"Fail to update open orders : {e}")

            await asyncio.sleep(self.ORDERS_REFRESH_TIME)

    async def resume(self) -> None:
        await super().resume()
        if not self.is_running:
            await self.run()


class CloseOrdersUpdater(OrdersProducer):
    CHANNEL_NAME = ORDERS_CHANNEL
    ORDERS_REFRESH_TIME = 72
    ORDERS_UPDATE_LIMIT = 10

    async def start(self):
        while not self.should_stop and not self.channel.is_paused:
            try:
                for symbol in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
                    close_orders: list = await self.channel.exchange_manager.exchange.get_closed_orders(
                        symbol=symbol,
                        limit=self.ORDERS_UPDATE_LIMIT)

                    if close_orders:
                        await self.push(orders=list(map(self.channel.exchange_manager.exchange.clean_order,
                                                        close_orders)),
                                        is_closed=True)
            except NotSupported:
                self.logger.warning(f"{self.channel.exchange_manager.exchange_name} is not supporting updates")
                await self.pause()
            except Exception as e:
                self.logger.error(f"Fail to update close orders : {e}")

            await asyncio.sleep(self.ORDERS_REFRESH_TIME)

    async def resume(self) -> None:
        await super().resume()
        if not self.is_running:
            await self.run()
