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

from octobot_trading.channels.positions import PositionsProducer
from octobot_trading.constants import POSITIONS_CHANNEL


class PositionsUpdater(PositionsProducer):
    CHANNEL_NAME = POSITIONS_CHANNEL
    POSITIONS_REFRESH_TIME = 11

    def __init__(self, channel):
        super().__init__(channel)
        self.should_use_open_position_per_symbol = False

    async def start(self):
        if not self._should_run():
            return

        # First fetch to define should_use_open_position_per_symbol
        try:
            await self.fetch_and_push()
        except NotImplementedError:
            self.logger.warning("Position updater cannot fetch positions : required methods are not implemented")
            await self.stop()

        while not self.should_stop:
            await asyncio.sleep(self.POSITIONS_REFRESH_TIME)
            try:
                if self.should_use_open_position_per_symbol:
                    await self.fetch_position_per_symbol()
                else:
                    await self.fetch_positions()

            except NotSupported:
                self.logger.warning(f"{self.channel.exchange_manager.exchange_name} is not supporting updates")
                await self.stop()
            except Exception as e:
                self.logger.exception(e, True, f"Fail to update positions : {e}")

    async def fetch_and_push(self):
        try:
            await self.fetch_positions()
        except NotImplementedError:
            self.should_use_open_position_per_symbol = True
            await self.fetch_position_per_symbol()

    def _should_run(self) -> bool:
        return self.channel.exchange_manager.is_future

    async def fetch_position_per_symbol(self):
        for symbol in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
            positions: list = await self.channel.exchange_manager.exchange.get_symbol_open_positions(symbol=symbol)
            if positions:
                await self.push(positions=positions, is_closed=False, is_liquidated=False)

    async def fetch_positions(self):
        for symbol, positions in (await self.channel.exchange_manager.exchange.get_open_positions()).items():
            if positions and symbol in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
                await self.push(positions=positions, is_closed=False, is_liquidated=False)

    async def resume(self) -> None:
        if not self._should_run():
            return
        await super().resume()
        if not self.is_running:
            await self.run()
