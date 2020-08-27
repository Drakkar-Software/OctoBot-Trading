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

# OpenOrdersUpdater and CloseOrdersUpdater are not triggering automatically like before: they are now triggered via a
# scheduler that will ensure that  each of its call is processed in its own time to prevent any concurrent call.
# This is possible if fetch_and_push from these classes are NOT creating tasks (otherwise the scheduler won't be able
# to know when an update is complete)
# At some point I was considering using an octobot channel as scheduler (a channel calling
# synchronized_perform_consumers_queue as in backtesting) but I'm not sure it's really appropriate, it will add a
# layer of complexity (queue and prio level) that we don't need. And it will make it harder to independently manage
# each symbol I think. Or maybe a simplified version that is also working in a synchronized way ?
# To be considered that we need an independent update loop for each symbol

# Therefore I would say that creating a simple scheduler as in the POC should be enough (with an update loop for
# each symbol)
# When to create this scheduler ? We will probably have the same need as with orders when handling positions,
# therefore I would say that a scheduler for each exchange (in REST) might do the job. Or maybe create it here when
# we need it ? No real inspiration here

# To be considered that we might need a manual update on open orders when running an on open order websocket (
# web disconnected for example): this should not require to be done in a scheduler since no order updater is started
# trigger_single_update() should be enough for this need.


class OpenOrdersUpdater(OrdersProducer):
    CHANNEL_NAME = ORDERS_CHANNEL
    ORDERS_STARTING_REFRESH_TIME = 10
    ORDERS_REFRESH_TIME = 14
    ORDERS_UPDATE_LIMIT = 200
    SHOULD_CHECK_MISSING_OPEN_ORDERS = True

    async def initialize(self):
        try:
            # create a scheduler loop (create scheduler if required ?) for each symbol and register
            # self.fetch_and_push()
            # trigger scheduler update for each symbol
            await self.fetch_and_push()
        except Exception as e:
            self.logger.error(f"Fail to initialize open orders : {e}")

    async def start(self):
        await self.initialize()
        await asyncio.sleep(self.ORDERS_STARTING_REFRESH_TIME)
        # remove loop (handled via scheduler)
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
            else:
                await self.handle_post_open_order_update(symbol, open_orders, False)

    async def resume(self) -> None:
        await super().resume()
        if not self.is_running:
            await self.run()

    # in stop: remove self.fetch_and_push for each symbol in scheduler
    # scheduler should stop when there is no users (like channel producers) to avoid extra computations


class CloseOrdersUpdater(OrdersProducer):
    CHANNEL_NAME = ORDERS_CHANNEL
    ORDERS_REFRESH_TIME = 32
    ORDERS_UPDATE_LIMIT = 200

    async def start(self):
        # create a scheduler loop (create scheduler if required ?) for each symbol and register
        # self.fetch_and_push()
        # trigger scheduler update for each symbol

        # remove loop (handled via scheduler)
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

    # in stop: remove self.fetch_and_push for each symbol in scheduler
    # scheduler should stop when there is no users (like channel producers) to avoid extra computations
