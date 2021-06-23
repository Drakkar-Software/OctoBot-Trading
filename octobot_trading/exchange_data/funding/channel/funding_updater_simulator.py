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
import octobot_trading.exchange_data.funding.channel.funding_updater as funding_updater
import octobot_trading.util as util


class FundingUpdaterSimulator(funding_updater.FundingUpdater):
    """
    The Funding Update Simulator simulates the exchange funding rate and send it to the Funding Channel
    """
    def __init__(self, channel):
        super().__init__(channel)
        self.time_consumer = None

    async def start(self):
        await self.resume()

    async def handle_timestamp(self, timestamp, **kwargs):
        for pair in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
            # TODO funding_rate ?
            await self._push_funding(symbol=pair, funding_rate=0, last_funding_time=timestamp)

    async def pause(self):
        await util.pause_time_consumer(self)

    async def stop(self):
        await util.stop_and_pause(self)

    async def resume(self):
        await util.resume_time_consumer(self, self.handle_timestamp)
