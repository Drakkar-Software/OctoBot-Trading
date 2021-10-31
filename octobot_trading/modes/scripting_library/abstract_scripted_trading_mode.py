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
import os

import octobot_trading.exchange_channel as exchanges_channel
import async_channel.channels as channels
import octobot_services.channel as services_channels
import octobot_trading.modes as trading_modes
import octobot_trading.constants as trading_constants
import octobot_trading.modes.scripting_library as scripting_library


class AbstractScriptedTradingMode(trading_modes.AbstractTradingMode):
    USER_COMMAND_RELOAD_SCRIPT = "reload_script"
    USER_COMMAND_RELOAD_SCRIPT_IS_LIVE = "is_live"


    def __init__(self, config, exchange_manager):
        super().__init__(config, exchange_manager)
        self.producer = AbstractScriptedTradingModeProducer
        self._live_script = None
        self._backtesting_script = None

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
        try:
            user_commands_consumer = \
                await channels.get_chan(services_channels.UserCommandsChannel.get_name()).new_consumer(
                    self._user_commands_callback,
                    {"bot_id": self.bot_id, "subject": self.get_name()}
                )
        except KeyError:
            return []
        return [user_commands_consumer]

    async def _user_commands_callback(self, bot_id, subject, action, data) -> None:
        self.logger.info(f"Received {action} command.")
        if action == AbstractScriptedTradingMode.USER_COMMAND_RELOAD_SCRIPT:
            live_script = data[AbstractScriptedTradingMode.USER_COMMAND_RELOAD_SCRIPT_IS_LIVE]
            await self.reload_script(live=live_script)

    @classmethod
    def get_is_symbol_wildcard(cls) -> bool:
        return False

    @classmethod
    def get_db_name(cls, bot_id):
        return f"{cls.__name__}_{bot_id}.json"

    def reload_script(self, live=True):
        raise NotImplementedError("reload_script is not implemented")

    def get_script(self, live=True):
        return self._live_script if live else self._backtesting_script

    def register_script(self, script, live=True):
        if live:
            self._live_script = script
        else:
            self._backtesting_script = script

    async def start_over_database(self):
        # todo dont move like this but add a check to ensure multiple subsequent moves dont happen when multiple symbols
        for producer in self.producers:
            producer.writer.close()
            os.rename(self.get_db_name(self.bot_id), self.get_db_name(f"{self.bot_id}_1"))
            producer.writer = scripting_library.DBWriter(self.get_db_name(self.bot_id))
            await producer.set_final_eval(*producer.last_call)


class AbstractScriptedTradingModeProducer(trading_modes.AbstractTradingModeProducer):

    def script_factory(self):
        raise NotImplementedError("script_factory is not set")

    def __init__(self, channel, config, trading_mode, exchange_manager):
        super().__init__(channel, config, trading_mode, exchange_manager)
        self.writer = scripting_library.DBWriter(self.trading_mode.get_db_name(self.trading_mode.bot_id))
        self.script_factory = self.trading_mode.get_script
        self.last_call = None
        self.traded_pair = trading_mode.symbol
        self.contexts = []

    async def set_final_eval(self, matrix_id: str, cryptocurrency: str, symbol: str, time_frame):
        context = scripting_library.Context(
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
            self.writer,
        )
        self.contexts.append(context)
        self.last_call = (matrix_id, cryptocurrency, symbol, time_frame)
        context.matrix_id = matrix_id
        context.cryptocurrency = cryptocurrency
        context.symbol = symbol
        context.time_frame = time_frame
        try:
            await self.script_factory()(context)
        finally:
            self.writer.are_data_initialized = True
            self.contexts.remove(context)
