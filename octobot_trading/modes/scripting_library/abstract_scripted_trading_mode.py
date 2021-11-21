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
import time
import contextlib
import importlib


import octobot_commons.logging as logging
import octobot_commons.databases as databases
import octobot_commons.enums as commons_enums
import octobot_commons.constants as commons_constants
import async_channel.channels as channels
import octobot_trading.exchange_channel as exchanges_channel
import octobot_trading.api as trading_api
import octobot_trading.modes as trading_modes
import octobot_trading.constants as trading_constants
import octobot_trading.enums as trading_enums
import octobot_trading.modes.scripting_library as scripting_library
import octobot_trading.errors as errors
import octobot_backtesting.api as backtesting_api


class AbstractScriptedTradingMode(trading_modes.AbstractTradingMode):
    TRADING_SCRIPT_MODULE = None
    BACKTESTING_SCRIPT_MODULE = None

    BACKTESTING_FILE_BY_BOT_ID = {}

    def __init__(self, config, exchange_manager):
        super().__init__(config, exchange_manager)
        self.producer = AbstractScriptedTradingModeProducer
        self._live_script = None
        self._backtesting_script = None
        self.timestamp = time.time()    # todo ensure multiple pairs conflicts
        self.script_name = None
        self.load_config()

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
            import octobot_services.channel as services_channels
            user_commands_consumer = \
                await channels.get_chan(services_channels.UserCommandsChannel.get_name()).new_consumer(
                    self._user_commands_callback,
                    {"bot_id": self.bot_id, "subject": self.get_name()}
                )
        except ImportError:
            self.logger.warning("Can't connect to services channels")
        except KeyError:
            return []
        return [user_commands_consumer]

    async def _user_commands_callback(self, bot_id, subject, action, data) -> None:
        self.logger.debug(f"Received {action} command.")
        if action == commons_enums.UserCommands.RELOAD_SCRIPT.value:
            await self.reload_script(live=True)
            await self.reload_script(live=False)

    @classmethod
    async def get_backtesting_plot(cls, run_id):
        ctx = scripting_library.Context.minimal(cls, logging.get_logger(cls.get_name()))
        return await cls.get_script_from_module(cls.BACKTESTING_SCRIPT_MODULE)(ctx, run_id)

    @classmethod
    def get_is_symbol_wildcard(cls) -> bool:
        return False

    @classmethod
    def get_db_folder(cls, backtesting=False, optimizer_id=None):
        root = os.path.join(commons_constants.USER_FOLDER, cls.__name__)
        if optimizer_id is None:
            return os.path.join(root, trading_constants.BACKTESTING) if backtesting else root
        else:
            return os.path.join(root, commons_constants.OPTIMIZER_RUNS_FOLDER, str(optimizer_id))

    @classmethod
    def init_db_folder(cls):
        if not os.path.exists(cls.get_db_folder()):
            os.makedirs(cls.get_db_folder())
        if not os.path.exists(cls.get_db_folder(backtesting=True)):
            os.makedirs(cls.get_db_folder(backtesting=True))

    @classmethod
    def register_prefix_for_bot(cls, bot_id, prefix):
        cls.BACKTESTING_FILE_BY_BOT_ID[bot_id] = prefix

    @classmethod
    def get_prefix(cls, bot_id):
        return cls.BACKTESTING_FILE_BY_BOT_ID[bot_id]

    @classmethod
    def get_db_name(cls, prefix=0, suffix=0, backtesting=False, metadata_db=False, bot_id=None, optimizer_id=None):
        if prefix == 0 and bot_id is not None:
            prefix = cls.get_prefix(bot_id)
        suffix_data = f"_{suffix}" if suffix != 0 else ""
        prefix_data = f"{prefix}_" if prefix != 0 else ""
        return os.path.join(cls.get_db_folder(backtesting=backtesting, optimizer_id=optimizer_id),
                            f"{'' if metadata_db else prefix_data}"
                            f"{trading_constants.METADATA_DB_FILE_NAME if metadata_db else trading_constants.DB_FILE_NAME}"
                            f"{suffix_data}.json")

    def get_script(self, live=True):
        return self._live_script if live else self._backtesting_script

    def register_script_module(self, script_module, live=True):
        if live:
            self.__class__.TRADING_SCRIPT_MODULE = script_module
            self._live_script = self.get_script_from_module(script_module)
        else:
            self.__class__.BACKTESTING_SCRIPT_MODULE = script_module
            self._backtesting_script = self.get_script_from_module(script_module)

    @staticmethod
    def get_script_from_module(module):
        return module.script

    async def reload_script(self, live=True):
        module = self.__class__.TRADING_SCRIPT_MODULE if live else self.__class__.BACKTESTING_SCRIPT_MODULE
        importlib.reload(module)
        self.register_script_module(module, live=live)
        # reload config
        self.load_config()
        if live:
            # todo cancel and restart live tasks
            await self.start_over_database(not live)

    def get_storage_db_name(self, with_suffix=False, backtesting=False, optimizer_id=None):
        if not with_suffix:
            try:
                # try getting an existing db
                self.get_db_name(prefix=self.BACKTESTING_FILE_BY_BOT_ID[self.bot_id],
                                 backtesting=backtesting, optimizer_id=optimizer_id)
            except KeyError:
                pass
        index = 1
        name_candidate = self.get_db_name(suffix=index, backtesting=backtesting, optimizer_id=optimizer_id) \
            if with_suffix else self.get_db_name(prefix=index, backtesting=backtesting, optimizer_id=optimizer_id)
        while index < 1000:
            if os.path.isfile(name_candidate):
                index += 1
                name_candidate = self.get_db_name(suffix=index, backtesting=backtesting, optimizer_id=optimizer_id) \
                    if with_suffix \
                    else self.get_db_name(prefix=index, backtesting=backtesting, optimizer_id=optimizer_id)
            else:
                if with_suffix is False:
                    self.register_prefix_for_bot(self.bot_id, index)
                return name_candidate
        raise RuntimeError("Impossible to find a new database name")

    async def start_over_database(self, backtesting):
        # todo dont move like this but add a check to ensure multiple subsequent moves dont happen when multiple symbols
        for producer in self.producers:
            await producer.writer.close()
            name_candidate = self.get_storage_db_name(backtesting=backtesting, with_suffix=True)
            os.rename(producer.writer.get_db_path(), name_candidate)
            producer.writer = databases.DBWriter(producer.writer.get_db_path())
            await producer.set_final_eval(*producer.last_call)

    @contextlib.asynccontextmanager
    async def get_metadata_writer(self, with_lock):
        file_path = self.get_db_name(backtesting=self.exchange_manager.backtesting,
                                     metadata_db=True,
                                     optimizer_id=self.get_optimizer_id())
        async with databases.DBWriter.database(file_path, with_lock=with_lock) as writer:
            yield writer

    def get_optimizer_id(self):
        return self.config.get(commons_constants.CONFIG_OPTIMIZER_ID)


class AbstractScriptedTradingModeProducer(trading_modes.AbstractTradingModeProducer):

    async def get_backtesting_metadata(self) -> dict:
        """
        Override this method to get add addition metadata
        :return: the metadata dict related to this backtesting run
        """
        profitability, profitability_percent, _, _, _ = trading_api.get_profitability_stats(self.exchange_manager)
        return {
            "id": self.trading_mode.get_prefix(self.trading_mode.bot_id),
            "p&l": float(profitability),
            "p&l%": float(profitability_percent),
            "trades": len(trading_api.get_trade_history(self.exchange_manager)),
            "timestamp": self.trading_mode.timestamp,
            "name": self.trading_mode.script_name,
            "user_inputs": self.trading_mode.trading_config,
            "backtesting_files": trading_api.get_backtesting_data_files(self.exchange_manager)
        }

    async def get_live_metadata(self):
        start_time = backtesting_api.get_backtesting_starting_time(self.exchange_manager.exchange.backtesting) \
            if trading_api.get_is_backtesting(self.exchange_manager) \
            else trading_api.get_exchange_current_time(self.exchange_manager)
        end_time = backtesting_api.get_backtesting_ending_time(self.exchange_manager.exchange.backtesting) \
            if trading_api.get_is_backtesting(self.exchange_manager) \
            else -1
        return {
            trading_enums.DBRows.REFERENCE_MARKET.value: trading_api.get_reference_market(self.config),
            trading_enums.DBRows.START_TIME.value: start_time,
            trading_enums.DBRows.END_TIME.value: end_time,
        }

    def __init__(self, channel, config, trading_mode, exchange_manager):
        super().__init__(channel, config, trading_mode, exchange_manager)
        self.trading_mode.init_db_folder()
        self.writer = databases.DBWriter(
            self.trading_mode.get_storage_db_name(with_suffix=False, backtesting=self.exchange_manager.backtesting,
                                                  optimizer_id=self.trading_mode.get_optimizer_id())
        )
        self.last_call = None
        self.traded_pair = trading_mode.symbol
        self.contexts = []
        self.are_metadata_saved = False

    async def set_final_eval(self, matrix_id: str, cryptocurrency: str, symbol: str, time_frame):
        context = scripting_library.Context(
            self.trading_mode,
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
            self.trading_mode.__class__,
            None,    # trigger_timestamp todo
            None,
            None,
        )
        self.contexts.append(context)
        self.last_call = (matrix_id, cryptocurrency, symbol, time_frame)
        context.matrix_id = matrix_id
        context.cryptocurrency = cryptocurrency
        context.symbol = symbol
        context.time_frame = time_frame
        try:
            if not self.writer.are_data_initialized:
                await scripting_library.save_metadata(self.writer, await self.get_live_metadata())
                await scripting_library.save_portfolio(self.writer, context)
            await self.trading_mode.get_script(live=True)(context)
        except errors.UnreachableExchange:
            raise
        except Exception as e:
            self.logger.exception(e, True, f"Error when running script: {e}")
        finally:
            if not self.exchange_manager.is_backtesting:
                # only update db after each run in live mode
                await self.writer.flush()
                if context.has_cache(context.traded_pair, context.time_frame):
                    await context.get_cache().flush()
            self.writer.are_data_initialized = True
            self.contexts.remove(context)

    async def stop(self) -> None:
        """
        Stop trading mode channels subscriptions
        """
        if not self.are_metadata_saved and self.exchange_manager.is_backtesting:     # todo ensure multiple pairs conflicts
            await self.writer.close()
            async with self.trading_mode.get_metadata_writer(with_lock=True) as writer:
                await scripting_library.save_metadata(writer, await self.get_backtesting_metadata())
                self.are_metadata_saved = True
        await super().stop()
