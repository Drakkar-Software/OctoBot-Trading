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

import octobot_trading.constants
import octobot_trading.enums as enums
import octobot_trading.errors
import octobot_trading.personal_data.state as state_class


class PositionState(state_class.State):
    def __init__(self, position, is_from_exchange_data):
        super().__init__(is_from_exchange_data)

        # ensure position has not been cleared
        if position.is_cleared():
            raise octobot_trading.errors.InvalidOrderState(f"Position has already been cleared. Position: {position}")

        # related position
        self.position = position

    def log_event_message(self, state_message, error=None):
        """
        Log a position state event
        """
        if state_message is enums.StatesMessages.ALREADY_SYNCHRONIZING:
            self.get_logger().debug(f"Trying to update a refreshing state for position: {self.position}")
        elif state_message is enums.StatesMessages.SYNCHRONIZING_ERROR:
            self.get_logger().exception(error, True, f"Error when synchronizing position {self.position}: {error}")
        else:
            self.get_logger().info(f"{self.position} {state_message.value} on "
                                   f"{self.position.exchange_manager.exchange_name}")

    async def _synchronize_with_exchange(self, force_synchronization: bool = False) -> None:
        pass # TODO

    def clear(self):
        """
        Clear references
        """
        self.position = None
