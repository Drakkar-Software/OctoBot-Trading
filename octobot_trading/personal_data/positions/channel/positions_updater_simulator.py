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

import octobot_commons.logging as logging
import octobot_trading.constants as constants
import octobot_trading.exchange_channel as exchanges_channel
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
            symbol_position = self.channel.exchange_manager.exchange_personal_data.positions_manager \
                .get_symbol_position(symbol=symbol)
            symbol_position.mark_price = mark_price
            await symbol_position.update_position_status(mark_price)
        except Exception as e:
            self.logger.exception(e, True, f"Fail to handle mark price : {e}")
