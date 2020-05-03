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
from octobot_trading.producers.funding_updater import FundingUpdater


class FundingUpdaterSimulator(FundingUpdater):
    """
    The Funding Update Simulator fetch the exchange funding rate and send it to the Funding Channel
    """

    async def before_update(self) -> (int, int):
        """
        Called to initialize funding update
        :return: the next funding time and the sleep time
        """
        await self.wait_for_processing()
        return await super(FundingUpdater, self).before_update()
