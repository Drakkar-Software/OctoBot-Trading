#  Drakkar-Software OctoBot
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

import octobot_trading.exchange_channel as exchanges_channel
import octobot_trading.modes as trading_modes
import octobot_trading.constants as trading_constants
import octobot_trading.modes.scripting_library as scripting_library


class AbstractScriptedTradingMode(trading_modes.AbstractTradingMode):
    def __init__(self, config, exchange_manager):
        super().__init__(config, exchange_manager)
        self.producer = AbstractScriptedTradingModeProducer

    def get_current_state(self) -> (str, float):
        return super().get_current_state()[0] if self.producers[0].state is None else self.producers[0].state.name, \
               "N/A"

    async def create_producers(self) -> list:
        mode_producer = self.producer(
            exchanges_channel.get_chan(trading_constants.MODE_CHANNEL, self.exchange_manager.id),
            self.config, self, self.exchange_manager)
        await mode_producer.run()
        return [mode_producer]

    async def create_consumers(self) -> list:
        return []

    @classmethod
    def get_is_symbol_wildcard(cls) -> bool:
        return False


class AbstractScriptedTradingModeProducer(trading_modes.AbstractTradingModeProducer):

    async def script(self, ctx: scripting_library.Context):
        raise NotImplementedError("script is not implemented")

    def __init__(self, channel, config, trading_mode, exchange_manager):
        super().__init__(channel, config, trading_mode, exchange_manager)
        self.traded_pair = trading_mode.symbol
        self.context = None

    async def set_final_eval(self, matrix_id: str, cryptocurrency: str, symbol: str, time_frame):
        if self.context is None:
            self.context = scripting_library.Context(
                self,
                self.exchange_manager,
                self.exchange_manager.trader,
                self.exchange_name,
                self.traded_pair,
                matrix_id,
                cryptocurrency,
                symbol,
                time_frame,
                self.logger,
            )
        if self.context.running:
            # nothing to do, the script is already activated
            return
        self.context.running = True
        self.context.matrix_id = matrix_id
        self.context.cryptocurrency = cryptocurrency
        self.context.symbol = symbol
        self.context.time_frame = time_frame
        try:
            await self.script(self.context)
        finally:
            self.context.running = False
