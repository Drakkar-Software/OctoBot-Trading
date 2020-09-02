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

from octobot_commons.logging.logging_util import get_logger

from octobot_trading.channels.exchange_channel import get_chan
from octobot_trading.constants import ORDERS_CHANNEL
from octobot_trading.enums import OrderStates
from octobot_trading.util.initializable import Initializable


class OrderState(Initializable):
    def __init__(self, order, is_from_exchange_data):
        super().__init__()

        # related order
        self.order = order

        # default state
        self.state = OrderStates.UNKNOWN

        # if this state has been created from exchange data or OctoBot internal mechanism
        self.is_from_exchange_data = is_from_exchange_data

        # order state lock
        self.lock = asyncio.Lock()

    def is_pending(self) -> bool:
        """
        :return: True if the state is pending for update
        """
        return self.state is OrderStates.UNKNOWN

    def is_refreshing(self) -> bool:
        """
        :return: True if the state is updating
        """
        return self.state is OrderStates.REFRESHING

    def is_open(self) -> bool:
        """
        :return: True if the Order is considered as open
        """
        return not (self.is_filled() or self.is_canceled() or self.is_closed())

    def is_filled(self) -> bool:
        """
        :return: True if the Order is considered as filled
        """
        return False

    def is_closed(self) -> bool:
        """
        :return: True if the Order is considered as closed
        """
        return False

    def is_canceled(self) -> bool:
        """
        :return: True if the Order is considered as canceled
        """
        return False

    def get_logger(self):
        """
        :return: the order logger
        """
        return get_logger(self.order.get_logger_name())

    def log_order_event_message(self, state_message):
        """
        Log an order state event
        """
        self.get_logger().info(f"{self.order} {state_message}"
                               f" on {self.order.exchange_manager.exchange_name}")

    async def initialize_impl(self) -> None:
        """
        Default OrderState initialization process
        """
        await self.update()

    async def terminate(self) -> None:
        """
        Implement the state ending process
        Can be portfolio updates, fees request, linked order cancellation, Trade creation etc...
        """
        raise NotImplementedError("terminate not implemented")

    async def update(self) -> None:
        """
        Update the order state
        Try to fix the pending state or terminate
        """
        if self.is_pending() and self.state is not OrderStates.REFRESHING:
            self.log_order_event_message("synchronizing")
            await self.synchronize()
        else:
            async with self.lock:
                await self.terminate()

    async def synchronize(self, force_synchronization=False, catch_exception=False) -> None:
        """
        Implement the exchange synchronization process
        Should begin by setting the state to REFRESHING
        Should end by :
        - calling terminate if the state is terminated
        - restoring the initial state if nothing has been changed with synchronization or if sync failed
        :param force_synchronization: When True, for the update of the order from the exchange
        """
        try:
            await self._synchronize_order_with_exchange(force_synchronization=force_synchronization)
        except Exception as e:
            if catch_exception:
                self.get_logger().exception(e, True, f"Error when synchronizing order {self.order}: {e}")
            else:
                raise

    async def _refresh_order_from_exchange(self, force_synchronization=False) -> bool:
        """
        Ask OrdersChannel Internal producer to refresh the order from the exchange
        :param force_synchronization: When True, for the update of the order from the exchange
        :return: the result of OrdersProducer.update_order_from_exchange()
        """
        return (await get_chan(ORDERS_CHANNEL, self.order.exchange_manager.id).get_internal_producer().
                update_order_from_exchange(order=self.order,
                                           wait_for_refresh=True,
                                           force_job_execution=force_synchronization))

    async def on_order_refresh_successful(self):
        """
        Called when _synchronize_order_with_exchange succeed to update the order
        """
        raise NotImplementedError("_on_order_refresh_successful not implemented")

    async def _synchronize_order_with_exchange(self, force_synchronization=False):
        """
        Ask the exchange to update the order
        Also manage the order state during the refreshing process
        :param force_synchronization: When True, for the update of the order from the exchange
        """
        previous_state = self.state
        async with self.lock:
            self.state = OrderStates.REFRESHING
        await self._refresh_order_from_exchange(force_synchronization=force_synchronization)
        async with self.lock:
            if self.state is OrderStates.REFRESHING:
                self.state = previous_state

    def clear(self):
        """
        Clear references
        """
        self.order = None
