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

    def is_pending(self) -> bool:
        """
        :return: True if the state is pending for update
        """
        return self.state is OrderStates.UNKNOWN

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

    async def initialize_impl(self) -> None:
        """
        Default OrderState initialization process
        Try to fix the pending state or terminate
        """
        if self.is_pending():
            await self.synchronize()
        else:
            await self.terminate()

    async def synchronize(self) -> None:
        """
        Implement the exchange synchronization process
        Should begin by setting the state to REFRESHING
        Should end by :
        - calling terminate if the state is terminated
        - restoring the initial state if nothing has been changed with synchronization or if sync failed
        """
        raise NotImplementedError("synchronize not implemented")

    async def terminate(self) -> None:
        """
        Implement the state ending process
        Can be portfolio updates, fees request, linked order cancellation, Trade creation etc...
        """
        raise NotImplementedError("terminate not implemented")

    async def _refresh_order_from_exchange(self) -> bool:
        """
        Ask OrdersChannel Internal producer to refresh the order from the exchange
        :return: the result of OrdersProducer.update_order_from_exchange()
        """
        return (await get_chan(ORDERS_CHANNEL, self.order.exchange_manager.id).get_internal_producer().
                update_order_from_exchange(self.order))

    async def _synchronize_order_with_exchange(self, on_refresh_successful_callback):
        """
        Ask the exchange to update the order
        Also manage the order state during the refreshing process
        :param on_refresh_successful_callback: the callback to be called when the refresh succeed
        """
        previous_state = self.state
        self.state = OrderStates.REFRESHING
        if await self._refresh_order_from_exchange():
            try:
                await on_refresh_successful_callback()
            except Exception:
                pass  # TODO
            finally:
                self.state = previous_state
        else:
            self.state = previous_state
