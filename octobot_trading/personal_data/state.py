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

import octobot_commons.logging as logging

import octobot_trading.enums as enums
import octobot_trading.util as util


class State(util.Initializable):
    def __init__(self, is_from_exchange_data):
        super().__init__()

        # default state
        self.state = enums.States.UNKNOWN

        # if this state has been created from exchange data or OctoBot internal mechanism
        self.is_from_exchange_data = is_from_exchange_data

        # state lock
        self.lock = asyncio.Lock()

    def is_pending(self) -> bool:
        """
        :return: True if the state is pending for update
        """
        return self.state is enums.States.UNKNOWN

    def is_refreshing(self) -> bool:
        """
        :return: True if the state is updating
        """
        return self.state is enums.States.REFRESHING

    def is_open(self) -> bool:
        """
        :return: True if the instance is considered as open
        """
        return not self.is_closed()

    def is_closed(self) -> bool:
        """
        :return: True if the instance is considered as closed
        """
        return False

    def get_logger(self):
        """
        :return: the instance logger
        """
        return logging.get_logger(self.__class__.__name__)

    def log_event_message(self, state_message, error=None):
        """
        Log a state event
        """
        self.get_logger().info(state_message.value)

    async def initialize_impl(self) -> None:
        """
        Default State initialization process
        """
        await self.update()

    async def should_be_updated(self) -> bool:
        """
        Defines if the instance should be updated
        :return: True if the instance should be updated when necessary
        """
        return True

    async def update(self) -> None:
        """
        Update the instance state if necessary
        Necessary when the state is not already synchronizing and when the instance should be updated
        Try to fix the pending state or terminate
        """
        if not self.is_refreshing():
            if self.is_pending() and not await self.should_be_updated():
                self.log_event_message(enums.StatesMessages.SYNCHRONIZING)
                await self.synchronize()
            else:
                async with self.lock:
                    await self.terminate()
        else:
            self.log_event_message(enums.StatesMessages.ALREADY_SYNCHRONIZING)

    async def synchronize(self, force_synchronization=False, catch_exception=False) -> None:
        """
        Implement the exchange synchronization process
        Should begin by setting the state to REFRESHING
        Should end by :
        - calling terminate if the state is terminated
        - restoring the initial state if nothing has been changed with synchronization or if sync failed
        :param force_synchronization: When True, for the update of the order from the exchange
        :param catch_exception: When False raises the Exception during synchronize_order instead of catching it silently
        """
        try:
            await self.synchronize_with_exchange(force_synchronization=force_synchronization)
        except Exception as e:
            if catch_exception:
                self.log_event_message(enums.StatesMessages.SYNCHRONIZING_ERROR, error=e)
            else:
                raise

    async def synchronize_with_exchange(self, force_synchronization: bool = False) -> None:
        """
        Ask the exchange to update the order only if the state is not already refreshing
        When the refreshing process starts set the state to enums.States.REFRESHING
        Restore the previous state if the refresh process fails
        :param force_synchronization: When True, for the update of the order from the exchange
        """
        if self.is_refreshing():
            self.log_event_message(enums.StatesMessages.ALREADY_SYNCHRONIZING)
        else:
            previous_state = self.state
            async with self.lock:
                self.state = enums.States.REFRESHING
            try:
                await self._synchronize_with_exchange(force_synchronization=force_synchronization)
            finally:
                async with self.lock:
                    if self.state is enums.States.REFRESHING:
                        self.state = previous_state

    async def _synchronize_with_exchange(self, force_synchronization: bool = False) -> None:
        """
        Called when state should be refreshed
        :param force_synchronization: When True, for the update of the order from the exchange
        """
        raise NotImplementedError("_synchronize_with_exchange not implemented")

    async def terminate(self) -> None:
        """
        Implement the state ending process
        Can be portfolio updates, fees request, linked order cancellation, Trade creation etc...
        """
        raise NotImplementedError("terminate not implemented")

    async def on_refresh_successful(self):
        """
        Called when synchronize succeed to update the instance
        """
        raise NotImplementedError("on_refresh_successful not implemented")

    def clear(self):
        """
        Clear references
        """
        raise NotImplementedError("clear not implemented")
