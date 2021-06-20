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
import octobot_trading.enums as enums
import octobot_trading.personal_data.positions.position_state as position_state


class ClosePositionState(position_state.PositionState):
    def __init__(self, position, is_from_exchange_data, force_close=True):
        super().__init__(position, is_from_exchange_data)
        self.state = enums.States.CLOSED if is_from_exchange_data or force_close or self.position.simulated \
            else enums.States.CLOSING

    async def initialize_impl(self, forced=False) -> None:
        if forced:
            self.state = enums.States.CLOSED
        return await super().initialize_impl()

    def is_pending(self) -> bool:
        return self.state is enums.States.CLOSING

    def is_closed(self) -> bool:
        return self.state is enums.States.CLOSED

    async def on_refresh_successful(self):
        """
        Verify the position is properly closed
        """
        if self.position.status is enums.PositionStatus.CLOSED:
            self.state = enums.States.CLOSED
            await self.update()

    async def terminate(self):
        """
        Add position to history
        """
        # TODO
