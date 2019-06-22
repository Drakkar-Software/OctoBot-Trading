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

from octobot_trading.channels.positions import PositionsProducer


class PositionsUpdater(PositionsProducer):
    POSITIONS_REFRESH_TIME = 2  # TODO = 10

    def __init__(self, channel):
        super().__init__(channel)
        self.should_stop = False
        self.channel = channel

    async def start(self):
        while not self.should_stop:
            try:
                for symbol in self.channel.exchange_manager.traded_pairs:
                    positions: list = await self.channel.exchange_manager.exchange.get_open_position(symbol=symbol)
                    if positions:
                        await self.push(positions)

            except Exception as e:
                self.logger.error(f"Fail to update positions : {e}")

            await asyncio.sleep(self.POSITIONS_REFRESH_TIME)

    def _cleanup_positions_dict(self, positions):
        for position in positions:
            try:
                pass  # TODO
            except KeyError as e:
                self.logger.error(f"Fail to cleanup position dict ({e})")
        return positions
