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
import copy

import octobot_commons.logging as logging

import octobot_trading.constants as constants
import octobot_trading.exchange_channel as exchanges_channel
import octobot_trading.personal_data.positions as positions
import octobot_trading.personal_data.positions.channel.positions_updater as positions_updater


class PositionsUpdaterSimulator(positions_updater.PositionsUpdater):
    async def start(self):
        if not self._should_run():
            return
        await self.initialize()

    async def initialize(self) -> None:
        """
        Initialize positions and future contracts
        """
        await self.initialize_contracts()
        self.channel.exchange_manager.exchange_personal_data.positions_manager.positions_initialized = True
        self.logger = logging.get_logger(f"{self.__class__.__name__}[{self.channel.exchange_manager.exchange.name}]")
        await exchanges_channel.get_chan(constants.MARK_PRICE_CHANNEL, self.channel.exchange_manager.id) \
            .new_consumer(self.handle_mark_price)
        self.channel.exchange_manager.exchange_personal_data.positions_manager.positions_initialized = True

    async def handle_mark_price(self, exchange: str, exchange_id: str, cryptocurrency: str, symbol: str, mark_price):
        """
        MarkPrice channel consumer callback
        """
        try:
            await self._update_positions_status(cryptocurrency=cryptocurrency, symbol=symbol, mark_price=mark_price)
        except Exception as e:
            self.logger.exception(e, True, f"Fail to handle mark price : {e}")

    async def _update_positions_status(self, cryptocurrency: str, symbol: str, mark_price):
        """
        Ask positions to check their status
        Ask liquidation and P&L update process if required
        """
        for position in copy.copy(
                self.channel.exchange_manager.exchange_personal_data.positions_manager.get_open_positions(
                    symbol=symbol)):
            await self._update_position_status(position, mark_price)

            if position.is_liquidated():
                await exchanges_channel.get_chan(constants.POSITIONS_CHANNEL, self.channel.exchange_manager.id) \
                    .get_internal_producer().send(cryptocurrency=cryptocurrency,
                                                  symbol=position.symbol,
                                                  order=position.to_dict(),
                                                  is_liquidated=position.is_liquidated(),
                                                  is_updated=False)

    async def _update_position_status(self, position: positions.Position, mark_price):
        """
        Call position status update
        """
        try:
            position.mark_price = mark_price
            await position.update_position_status()

            if position.is_liquidated():
                self.logger.debug(f"{position.symbol} (ID : {position.position_id})"
                                  f" liquidated on {self.channel.exchange.name} at {position.mark_price} ")
        except Exception as e:
            self.logger.exception(e, True, f"Fail to update position status : {e} (concerned position : {position}).")
