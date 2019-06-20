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

from octobot_trading.channels.orders import OrdersProducer
from octobot_trading.enums import ExchangeConstantsOrderColumns


class OrdersUpdater(OrdersProducer):
    ORDERS_STARTING_REFRESH_TIME = 10
    ORDERS_REFRESH_TIME = 2  # TODO = 10
    ORDERS_UPDATE_LIMIT = 10

    def __init__(self, channel):
        super().__init__(channel)
        self.should_stop = False
        self.channel = channel

    async def initialize(self):
        try:
            open_orders: list = await self.channel.exchange_manager.exchange.get_open_orders()
            await self.push(self._cleanup_open_orders_dict(open_orders))
            await asyncio.sleep(self.ORDERS_STARTING_REFRESH_TIME)
        except Exception as e:
            self.logger.exception(f"Fail to initialize open orders : {e}")

    async def start(self):
        await self.initialize()
        while not self.should_stop:
            try:
                open_orders: list = await self.channel.exchange_manager.exchange.get_open_orders(limit=self.ORDERS_UPDATE_LIMIT)
                await self.push(self._cleanup_open_orders_dict(open_orders))
                await asyncio.sleep(self.ORDERS_REFRESH_TIME)
            except Exception as e:
                self.logger.exception(f"Fail to update open orders : {e}")

    def _cleanup_open_orders_dict(self, open_orders):
        for open_order in open_orders:
            try:
                open_order.pop(ExchangeConstantsOrderColumns.INFO.value)
            except KeyError as e:
                self.logger.error(f"Fail to cleanup open order dict ({e})")
        return open_orders
