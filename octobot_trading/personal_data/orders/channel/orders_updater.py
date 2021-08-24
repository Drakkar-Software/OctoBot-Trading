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

import octobot_commons.async_job as async_job

import octobot_trading.errors as errors
import octobot_trading.personal_data.orders.channel.orders as orders_channel
import octobot_trading.constants as constants


class OrdersUpdater(orders_channel.OrdersProducer):
    """
    Update open and close orders from exchange
    Can also be used to update a specific order from exchange
    """

    CHANNEL_NAME = constants.ORDERS_CHANNEL
    ORDERS_UPDATE_LIMIT = 200
    ORDERS_STARTING_REFRESH_TIME = 10
    OPEN_ORDER_REFRESH_TIME = 7
    CLOSE_ORDER_REFRESH_TIME = 81
    TIME_BETWEEN_ORDERS_REFRESH = 2

    def __init__(self, channel):
        super().__init__(channel)

        # create async jobs
        self.open_orders_job = async_job.AsyncJob(self._open_orders_fetch_and_push,
                                                  execution_interval_delay=self.OPEN_ORDER_REFRESH_TIME,
                                                  min_execution_delay=self.TIME_BETWEEN_ORDERS_REFRESH)
        self.closed_orders_job = async_job.AsyncJob(self._closed_orders_fetch_and_push,
                                                    execution_interval_delay=self.CLOSE_ORDER_REFRESH_TIME,
                                                    min_execution_delay=self.TIME_BETWEEN_ORDERS_REFRESH)
        self.order_update_job = async_job.AsyncJob(self._order_fetch_and_push,
                                                   is_periodic=False,
                                                   enable_multiple_runs=True)
        self.order_update_job.add_job_dependency(self.open_orders_job)
        self.open_orders_job.add_job_dependency(self.order_update_job)

    async def initialize(self) -> None:
        """
        Initialize data before starting jobs
        """
        try:
            await self.fetch_and_push(is_from_bot=False)
        except errors.NotSupported:
            self.logger.error(f"{self.channel.exchange_manager.exchange_name} is not supporting open orders updates")
            await self.pause()
        except Exception as e:
            self.logger.error(f"Fail to initialize orders : {e}")
        finally:
            self.channel.exchange_manager.exchange_personal_data.orders_manager.are_exchange_orders_initialized = True

    async def start(self) -> None:
        """
        Start updater jobs
        """
        await self.initialize()
        await asyncio.sleep(self.ORDERS_STARTING_REFRESH_TIME)
        await self.open_orders_job.run()
        # await self.closed_orders_job.run()

    async def fetch_and_push(self, is_from_bot=True, limit=ORDERS_UPDATE_LIMIT):
        """
        Update open and closed orders from exchange
        :param is_from_bot: True if the order was created by OctoBot
        :param limit: the exchange request orders count limit
        """
        # should not raise: open orders are necessary
        await self._open_orders_fetch_and_push(is_from_bot=is_from_bot, limit=limit)
        await asyncio.sleep(self.TIME_BETWEEN_ORDERS_REFRESH)
        try:
            # can raise, closed orders are not critical data
            await self._closed_orders_fetch_and_push(limit=limit)
        except errors.NotSupported:
            self.logger.debug(f"{self.channel.exchange_manager.exchange_name} is not supporting closed orders updates")

    async def _open_orders_fetch_and_push(self, is_from_bot=True, limit=ORDERS_UPDATE_LIMIT):
        """
        Update open orders from exchange
        :param is_from_bot: True if the order was created by OctoBot
        :param limit: the exchange request orders count limit
        """
        for symbol in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
            open_orders: list = await self.channel.exchange_manager.exchange.get_open_orders(symbol=symbol, limit=limit)
            if open_orders:
                await self.push(orders=list(map(self.channel.exchange_manager.exchange.clean_order, open_orders)),
                                is_from_bot=is_from_bot)
            else:
                await self.handle_post_open_order_update(symbol, open_orders, False)

    async def _closed_orders_fetch_and_push(self, limit=ORDERS_UPDATE_LIMIT) -> None:
        """
        Update closed orders from exchange
        :param limit: the exchange request orders count limit
        """
        for symbol in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
            close_orders: list = await self.channel.exchange_manager.exchange.get_closed_orders(
                symbol=symbol, limit=limit)

            if close_orders:
                await self.push(orders=list(map(self.channel.exchange_manager.exchange.clean_order, close_orders)),
                                are_closed=True)

    async def update_order_from_exchange(self, order,
                                         should_notify=False,
                                         wait_for_refresh=False,
                                         force_job_execution=False,
                                         create_order_producer_if_missing=True):
        """
        Trigger order job refresh from exchange
        :param order: the order to update
        :param wait_for_refresh: if True, wait until the order refresh task to finish
        :param should_notify: if Orders channel consumers should be notified
        :param force_job_execution: When True, order_update_job will bypass its dependencies check
        :param create_order_producer_if_missing: Should be set to False when called by self to prevent spamming
        :return: True if the order was updated
        """
        await self.order_update_job.run(force=True, wait_for_task_execution=wait_for_refresh,
                                        ignore_dependencies_check=force_job_execution,
                                        order=order, should_notify=should_notify)

    async def _order_fetch_and_push(self, order, should_notify=False):
        """
        Update Order from exchange
        :param order: the order to update
        :param should_notify: if Orders channel consumers should be notified
        :return: True if the order was updated
        """
        exchange_name = order.exchange_manager.exchange_name if order.exchange_manager else "cleared order's exchange"
        self.logger.debug(f"Requested update for {order} on {exchange_name}")
        raw_order = await self.channel.exchange_manager.exchange.get_order(order.order_id, order.symbol)

        if raw_order is not None:
            raw_order = self.channel.exchange_manager.exchange.clean_order(raw_order)
            self.logger.debug(f"Received update for {order} on {exchange_name}: {raw_order}")

            await self.channel.exchange_manager.exchange_personal_data.handle_order_update_from_raw(
                order.order_id, raw_order, should_notify=should_notify)

    async def stop(self) -> None:
        """
        Stop producer by stopping its jobs
        """
        await super().stop()
        self.open_orders_job.stop()
        self.closed_orders_job.stop()
        self.order_update_job.stop()

    async def resume(self) -> None:
        """
        Resume producer by restarting its jobs
        """
        await super().resume()
        if not self.is_running:
            await self.run()
