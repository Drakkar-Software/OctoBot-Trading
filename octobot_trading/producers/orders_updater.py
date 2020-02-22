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

from octobot_trading.constants import ORDERS_CHANNEL
from octobot_trading.channels.orders import OrdersProducer
from octobot_trading.enums import ExchangeConstantsOrderColumns


class OpenOrdersUpdater(OrdersProducer):
    CHANNEL_NAME = ORDERS_CHANNEL
    ORDERS_STARTING_REFRESH_TIME = 10
    ORDERS_REFRESH_TIME = 18
    ORDERS_UPDATE_LIMIT = 10

    async def initialize(self):
        try:
            for symbol in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
                open_orders: list = await self.channel.exchange_manager.exchange.get_open_orders(symbol=symbol)

                if open_orders:
                    await self.push(self._cleanup_open_orders_dict(open_orders), is_from_bot=False)

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
                        await self.push(self._cleanup_open_orders_dict(open_orders))
            except NotSupported:
                self.logger.warning(f"{self.channel.exchange_manager.exchange_name} is not supporting updates")
                await self.pause()
            except Exception as e:
                self.logger.error(f"Fail to update open orders : {e}")

            await asyncio.sleep(self.ORDERS_REFRESH_TIME)

    def _cleanup_open_orders_dict(self, open_orders):
        for open_order in open_orders:
            try:
                open_order.pop(ExchangeConstantsOrderColumns.INFO.value)
                exchange_timestamp = open_order[ExchangeConstantsOrderColumns.TIMESTAMP.value]
                open_order[ExchangeConstantsOrderColumns.TIMESTAMP.value] = \
                    self.channel.exchange_manager.get_uniformized_timestamp(exchange_timestamp)
            except KeyError as e:
                self.logger.error(f"Fail to cleanup open order dict ({e})")
        return open_orders

    async def resume(self) -> None:
        await super().resume()
        if not self.is_running:
            await self.run()


class CloseOrdersUpdater(OrdersProducer):
    CHANNEL_NAME = ORDERS_CHANNEL
    ORDERS_REFRESH_TIME = 2  # TODO = 10
    ORDERS_UPDATE_LIMIT = 10

    async def start(self):
        while not self.should_stop and not self.channel.is_paused:
            try:
                for symbol in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
                    close_orders: list = await self.channel.exchange_manager.exchange.get_closed_orders(
                        symbol=symbol,
                        limit=self.ORDERS_UPDATE_LIMIT)

                    if close_orders:
                        await self.push(self._cleanup_close_orders_dict(close_orders), is_closed=True)
            except NotSupported:
                self.logger.warning(f"{self.channel.exchange_manager.exchange_name} is not supporting updates")
                await self.pause()
            except Exception as e:
                self.logger.error(f"Fail to update close orders : {e}")

            await asyncio.sleep(self.ORDERS_REFRESH_TIME)

    def _cleanup_close_orders_dict(self, close_orders):
        for close_order in close_orders:
            try:
                close_order.pop(ExchangeConstantsOrderColumns.INFO.value)
            except KeyError as e:
                self.logger.error(f"Fail to cleanup close order dict ({e})")
        return close_orders

    async def resume(self) -> None:
        await super().resume()
        if not self.is_running:
            await self.run()
