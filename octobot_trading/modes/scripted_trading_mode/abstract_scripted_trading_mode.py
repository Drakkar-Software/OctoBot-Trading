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
import time
import contextlib
import importlib
import asyncio

import octobot_commons.logging as logging
import octobot_commons.databases as databases
import octobot_commons.enums as commons_enums
import octobot_commons.errors as commons_errors
import octobot_commons.constants as commons_constants
import octobot_commons.channels_name as channels_name
import octobot_commons.optimization_campaign as optimization_campaign
import async_channel.channels as channels
import octobot_trading.exchange_channel as exchanges_channel
import octobot_trading.api as trading_api
import octobot_trading.modes.abstract_trading_mode as abstract_trading_mode
import octobot_trading.modes.channel as modes_channel
import octobot_trading.modes.context_management as context_management
import octobot_trading.modes.basic_keywords as basic_keywords
import octobot_trading.constants as trading_constants
import octobot_trading.enums as trading_enums
import octobot_trading.errors as errors
import octobot_trading.personal_data as personal_data
import octobot_backtesting.api as backtesting_api
import octobot_tentacles_manager.api as tentacles_manager_api


class AbstractScriptedTradingMode(abstract_trading_mode.AbstractTradingMode):
    TRADING_SCRIPT_MODULE = None
    BACKTESTING_SCRIPT_MODULE = None

    BACKTESTING_ID_BY_BOT_ID = {}
    INITIALIZED_DB_BY_BOT_ID = {}
    SAVED_RUN_METADATA_DB_BY_BOT_ID = {}
    WRITER_IDENTIFIER_BY_BOT_ID = {}
    INITIALIZED_TRADING_PAIR_BY_BOT_ID = {}

    def __init__(self, config, exchange_manager):
        super().__init__(config, exchange_manager)
        self.producer = AbstractScriptedTradingModeProducer
        self._live_script = None
        self._backtesting_script = None
        self.timestamp = time.time()
        self.script_name = None

        if exchange_manager:
            self.load_config()
            # add config folder to importable files to import the user script
            tentacles_manager_api.import_user_tentacles_config_folder(self.exchange_manager.tentacles_setup_config)

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
            await exchanges_channel.get_chan(channels_name.OctoBotTradingChannelsName.TRADES_CHANNEL.value,
                                             self.exchange_manager.id).new_consumer(
                self._trades_callback,
                symbol=self.symbol
            )
            import octobot_services.channel as services_channels
            user_commands_consumer = \
                await channels.get_chan(services_channels.UserCommandsChannel.get_name()).new_consumer(
                    self._user_commands_callback,
                    {"bot_id": self.bot_id, "subject": self.get_name()}
                )
            return [user_commands_consumer]
        except ImportError:
            self.logger.warning("Can't connect to services channels")
        except KeyError:
            return []
        return []

    async def _trades_callback(
            self,
            exchange: str,
            exchange_id: str,
            cryptocurrency: str,
            symbol: str,
            trade: dict,
            old_trade: bool,
    ):
        if trade[trading_enums.ExchangeConstantsOrderColumns.STATUS.value] != trading_enums.OrderStatus.CANCELED.value:
            await basic_keywords.store_trade(None, trade, exchange_manager=self.exchange_manager,
                                             writer=self.producers[0].trades_writer)

    async def _user_commands_callback(self, bot_id, subject, action, data) -> None:
        self.logger.debug(f"Received {action} command.")
        if action == commons_enums.UserCommands.RELOAD_SCRIPT.value:
            await self.reload_script(live=True)
            await self.reload_script(live=False)
        elif action == commons_enums.UserCommands.CLEAR_PLOTTING_CACHE.value:
            await self.clear_plotting_cache()
        elif action == commons_enums.UserCommands.CLEAR_ALL_CACHE.value:
            await self.clear_all_cache()
        elif action == commons_enums.UserCommands.CLEAR_SIMULATED_ORDERS_CACHE.value:
            await self.clear_simulated_orders_cache()
        elif action == commons_enums.UserCommands.CLEAR_SIMULATED_TRADES_CACHE.value:
            await self.clear_simulated_trades_cache()
        elif action == commons_enums.UserCommands.CLEAR_SIMULATED_TRANSACTIONS_CACHE.value:
            await self.clear_simulated_transactions_cache()

    async def clear_simulated_orders_cache(self):
        for producer in self.producers:
            await basic_keywords.clear_orders_cache(producer.orders_writer)

    async def clear_simulated_trades_cache(self):
        for producer in self.producers:
            await basic_keywords.clear_trades_cache(producer.trades_writer)

    async def clear_simulated_transactions_cache(self):
        for producer in self.producers:
            await basic_keywords.clear_transactions_cache(producer.transactions_cache)

    async def clear_all_cache(self):

        for tentacle_name in [self.get_name()] + [evaluator.get_name() for evaluator in
                                                  self.called_nested_evaluators]:
            await databases.CacheManager().clear_cache(tentacle_name)

    async def clear_plotting_cache(self):
        for producer in self.producers:
            await basic_keywords.clear_all_tables(producer.symbol_writer)

    @classmethod
    async def get_backtesting_plot(cls, exchange, symbol, backtesting_id, optimizer_id, optimization_campaign):
        ctx = context_management.Context.minimal(cls({}, None), logging.get_logger(cls.get_name()), exchange, symbol,
                                                 backtesting_id, optimizer_id, optimization_campaign)
        return await cls.get_script_from_module(cls.BACKTESTING_SCRIPT_MODULE)(ctx)

    @classmethod
    def get_is_symbol_wildcard(cls) -> bool:
        return False

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
            await self.start_over_database()

    async def start_over_database(self):
        await self.clear_plotting_cache()
        for producer in self.producers:
            for time_frame, call_args in producer.last_call_by_timeframe.items():
                await basic_keywords.clear_user_inputs(producer.run_data_writer)
                await producer.init_user_inputs(False)
                producer.run_data_writer.set_initialized_flags(False, (time_frame, ))
                last_call_timestamp = call_args[3]
                producer.symbol_writer.set_initialized_flags(False, (last_call_timestamp,))
                self.__class__.INITIALIZED_DB_BY_BOT_ID[self.bot_id] = False
                await self.close_caches(reset_cache_db_ids=True)
                await producer.call_script(*call_args)

    def get_optimizer_id(self):
        return self.config.get(commons_constants.CONFIG_OPTIMIZER_ID)

    @classmethod
    async def get_backtesting_id(cls, bot_id, config=None, generate_if_not_found=False, tentacles_setup_config=None):
        try:
            return cls.BACKTESTING_ID_BY_BOT_ID[bot_id]
        except KeyError:
            if generate_if_not_found:
                try:
                    backtesting_id = config.get(commons_constants.CONFIG_BACKTESTING_ID) \
                                     or await cls._generate_new_backtesting_id(tentacles_setup_config)
                    cls.BACKTESTING_ID_BY_BOT_ID[bot_id] = backtesting_id
                    return backtesting_id
                except AttributeError:
                    raise RuntimeError("config is required when a backtesting_id is not registered with a bot id")
            raise RuntimeError(f"No backtesting id for bot_id: {bot_id}")

    @classmethod
    async def _generate_new_backtesting_id(cls, tentacles_setup_config):
        db_manager = databases.DatabaseManager(
            cls,
            optimization_campaign.OptimizationCampaign.get_campaign_name(tentacles_setup_config)
        )
        db_manager.backtesting_id = await db_manager.generate_new_backtesting_id()
        # initialize to lock the backtesting id
        await db_manager.initialize()
        return db_manager.backtesting_id

    def get_writer(self, writer_identifier):
        try:
            return self.__class__.WRITER_IDENTIFIER_BY_BOT_ID[self.bot_id][writer_identifier]
        except KeyError:
            if self.bot_id not in self.__class__.WRITER_IDENTIFIER_BY_BOT_ID:
                self.__class__.WRITER_IDENTIFIER_BY_BOT_ID[self.bot_id] = {}
            writer = databases.DBWriterReader(writer_identifier)
            self.__class__.WRITER_IDENTIFIER_BY_BOT_ID[self.bot_id][writer_identifier] = writer
            return writer

    async def close_writer(self, writer_identifier):
        try:
            await self.__class__.WRITER_IDENTIFIER_BY_BOT_ID[self.bot_id][writer_identifier].close()
            self.__class__.WRITER_IDENTIFIER_BY_BOT_ID[self.bot_id].pop(writer_identifier)
        except KeyError:
            pass

    def set_initialized_trading_pair_by_bot_id(self, symbol, time_frame, initialized):
        try:
            self.__class__.INITIALIZED_TRADING_PAIR_BY_BOT_ID[self.bot_id][self.exchange_manager.exchange_name][
                symbol][time_frame] = initialized
        except KeyError:
            if self.bot_id not in self.__class__.INITIALIZED_TRADING_PAIR_BY_BOT_ID:
                self.__class__.INITIALIZED_TRADING_PAIR_BY_BOT_ID[self.bot_id] = {}
            if self.exchange_manager.exchange_name not in \
                    self.__class__.INITIALIZED_TRADING_PAIR_BY_BOT_ID[self.bot_id]:
                self.__class__.INITIALIZED_TRADING_PAIR_BY_BOT_ID[self.bot_id][self.exchange_manager.exchange_name] = {}
            if symbol not in \
                    self.__class__.INITIALIZED_TRADING_PAIR_BY_BOT_ID[self.bot_id][self.exchange_manager.exchange_name]:
                self.__class__.INITIALIZED_TRADING_PAIR_BY_BOT_ID[self.bot_id][
                    self.exchange_manager.exchange_name][symbol] = {}
            if time_frame not in \
                    self.__class__.INITIALIZED_TRADING_PAIR_BY_BOT_ID[self.bot_id][self.exchange_manager.exchange_name][
                        symbol]:
                self.__class__.INITIALIZED_TRADING_PAIR_BY_BOT_ID[self.bot_id][self.exchange_manager.exchange_name][
                    symbol][time_frame] = initialized

    def get_initialized_trading_pair_by_bot_id(self, symbol, time_frame):
        return self.__class__.INITIALIZED_TRADING_PAIR_BY_BOT_ID[self.bot_id][self.exchange_manager.exchange_name][
                symbol][time_frame]


class AbstractScriptedTradingModeProducer(modes_channel.AbstractTradingModeProducer):

    async def get_backtesting_metadata(self, user_inputs) -> dict:
        """
        Override this method to get add addition metadata
        :return: the metadata dict related to this backtesting run
        """
        symbols = trading_api.get_trading_pairs(self.exchange_manager)
        profitability, profitability_percent, _, _, _ = trading_api.get_profitability_stats(self.exchange_manager)
        origin_portfolio = personal_data.portfolio_to_float(
            self.exchange_manager.exchange_personal_data.portfolio_manager.
            portfolio_value_holder.origin_portfolio.portfolio)
        end_portfolio = personal_data.portfolio_to_float(
            self.exchange_manager.exchange_personal_data.portfolio_manager.portfolio.portfolio)
        for portfolio in (origin_portfolio, end_portfolio):
            for values in portfolio.values():
                values.pop("available", None)
        if self.exchange_manager.is_future:
            for position in self.exchange_manager.exchange_personal_data.positions_manager.positions.values():
                end_portfolio[position.get_currency()]["position"] = float(position.quantity)
        time_frames = [tf.value
                       for tf in trading_api.get_exchange_available_required_time_frames(self.exchange_name,
                                                                                         self.exchange_manager.id)]
        formatted_user_inputs = {}
        for user_input in user_inputs:
            if not user_input["is_nested_config"]:
                try:
                    formatted_user_inputs[user_input["tentacle"]][user_input["name"]] = user_input["value"]
                except KeyError:
                    formatted_user_inputs[user_input["tentacle"]] = {
                        user_input["name"]: user_input["value"]
                    }
        leverage = 0
        if self.exchange_manager.is_future and hasattr(self.exchange_manager.exchange, "get_pair_future_contract"):
            leverage = float(self.exchange_manager.exchange.get_pair_future_contract(symbols[0]).current_leverage)
        trades = trading_api.get_trade_history(self.exchange_manager)
        entries = [
            trade
            for trade in trades
            if trade.status is trading_enums.OrderStatus.FILLED and trade.side is trading_enums.TradeOrderSide.BUY
        ]
        win_rate = round(float(trading_api.get_win_rate(self.exchange_manager) * 100), 3)
        wins = round(win_rate * len(entries) / 100)
        return {
            trading_enums.BacktestingMetadata.OPTIMIZATION_CAMPAIGN.value:
                self.database_manager.optimization_campaign_name,
            trading_enums.BacktestingMetadata.ID.value: await self.trading_mode.get_backtesting_id(
                self.trading_mode.bot_id),
            trading_enums.BacktestingMetadata.GAINS.value: round(float(profitability), 8),
            trading_enums.BacktestingMetadata.PERCENT_GAINS.value: round(float(profitability_percent), 3),
            trading_enums.BacktestingMetadata.END_PORTFOLIO.value: str(end_portfolio),
            trading_enums.BacktestingMetadata.START_PORTFOLIO.value: str(origin_portfolio),
            trading_enums.BacktestingMetadata.WIN_RATE.value: win_rate,
            trading_enums.BacktestingMetadata.SYMBOLS.value: symbols,
            trading_enums.BacktestingMetadata.TIME_FRAMES.value: time_frames,
            trading_enums.BacktestingMetadata.START_TIME.value: backtesting_api.get_backtesting_starting_time(
                self.exchange_manager.exchange.backtesting),
            trading_enums.BacktestingMetadata.END_TIME.value: backtesting_api.get_backtesting_ending_time(
                self.exchange_manager.exchange.backtesting),
            trading_enums.BacktestingMetadata.ENTRIES.value: len(entries),
            trading_enums.BacktestingMetadata.WINS.value: wins,
            trading_enums.BacktestingMetadata.LOSES.value: len(entries) - wins,
            trading_enums.BacktestingMetadata.TRADES.value: len(trades),
            trading_enums.BacktestingMetadata.TIMESTAMP.value: self.trading_mode.timestamp,
            trading_enums.BacktestingMetadata.NAME.value: self.trading_mode.script_name,
            trading_enums.BacktestingMetadata.LEVERAGE.value: leverage,
            trading_enums.BacktestingMetadata.USER_INPUTS.value: formatted_user_inputs,
            trading_enums.BacktestingMetadata.BACKTESTING_FILES.value: trading_api.get_backtesting_data_files(
                self.exchange_manager)
        }

    async def get_live_metadata(self):
        start_time = backtesting_api.get_backtesting_starting_time(self.exchange_manager.exchange.backtesting) \
            if trading_api.get_is_backtesting(self.exchange_manager) \
            else trading_api.get_exchange_current_time(self.exchange_manager)
        end_time = backtesting_api.get_backtesting_ending_time(self.exchange_manager.exchange.backtesting) \
            if trading_api.get_is_backtesting(self.exchange_manager) \
            else -1
        exchange_type = "spot"
        exchanges = [self.exchange_name]  # TODO multi exchange
        future_contracts_by_exchange = {}
        if self.exchange_manager.is_future and hasattr(self.exchange_manager.exchange, "pair_contracts"):
            exchange_type = "future"
            future_contracts_by_exchange = {
                self.exchange_name: {
                    symbol: {
                        "contract_type": contract.contract_type.value,
                        "position_mode": contract.position_mode.value,
                        "margin_type": contract.margin_type.value
                    } for symbol, contract in self.exchange_manager.exchange.pair_contracts.items()
                }
            }
        return {
            trading_enums.DBRows.REFERENCE_MARKET.value: trading_api.get_reference_market(self.config),
            trading_enums.DBRows.START_TIME.value: start_time,
            trading_enums.DBRows.END_TIME.value: end_time,
            trading_enums.DBRows.TRADING_TYPE.value: exchange_type,
            trading_enums.DBRows.EXCHANGES.value: exchanges,
            trading_enums.DBRows.FUTURE_CONTRACTS.value: future_contracts_by_exchange,
        }

    def __init__(self, channel, config, trading_mode, exchange_manager):
        super().__init__(channel, config, trading_mode, exchange_manager)
        self.last_call_by_timeframe = {}
        self.traded_pair = trading_mode.symbol
        self.are_metadata_saved = False

    async def start(self) -> None:
        await super().start()
        backtesting_id = await self.trading_mode.get_backtesting_id(
            self.trading_mode.bot_id, self.trading_mode.config, generate_if_not_found=True,
            tentacles_setup_config=self.trading_mode.exchange_manager.tentacles_setup_config) \
            if self.exchange_manager.is_backtesting else None
        self.database_manager = databases.DatabaseManager(
            self.trading_mode.__class__,
            optimization_campaign.OptimizationCampaign.get_campaign_name(
                self.trading_mode.exchange_manager.tentacles_setup_config
            ),
            backtesting_id=backtesting_id,
            optimizer_id=self.trading_mode.get_optimizer_id()
        )
        await self.database_manager.initialize(self.exchange_name)
        self.run_data_writer = self.trading_mode.get_writer(self.database_manager.get_run_data_db_identifier())
        # refresh user inputs
        await self.init_user_inputs(True)
        self.orders_writer = self.trading_mode.get_writer(self.database_manager.get_orders_db_identifier(
            self.exchange_name
        ))
        self.trades_writer = self.trading_mode.get_writer(self.database_manager.get_trades_db_identifier(
            self.exchange_name
        ))
        self.transactions_writer = self.trading_mode.get_writer(self.database_manager.get_transactions_db_identifier(
            self.exchange_name
        ))
        self.symbol_writer = self.trading_mode.get_writer(self.database_manager.get_symbol_db_identifier(
            self.exchange_name,
            self.traded_pair
        ))
        await self._trigger_initialization_call()

    async def _trigger_initialization_call(self):
        # initialization call is a special call that does not trigger trades and allows the script
        # to be run at least once in order to initialize its configuration
        if self.exchange_manager.is_backtesting:
            # not necessary in backtesting
            return

        # fake an evaluator call
        cryptocurrency, symbol, time_frame, trigger_time = self._get_initialization_call_args()
        await self.call_script(self.matrix_id, cryptocurrency, symbol, time_frame,
                               commons_enums.ActivationTopics.EVALUATORS.value, trigger_time, init_call=True)

    def _get_initialization_call_args(self):
        currency = next(iter(self.exchange_manager.exchange_config.traded_cryptocurrencies))
        symbol = self.exchange_manager.exchange_config.traded_cryptocurrencies[currency][0]
        time_frame = self.exchange_manager.exchange_config.traded_time_frames[0]
        current_time = self.exchange_manager.exchange.get_exchange_current_time()
        trigger_time = current_time - current_time \
            % (commons_enums.TimeFramesMinutes[time_frame] * commons_constants.MINUTE_TO_SECONDS)
        return currency, symbol, time_frame.value, trigger_time

    async def ohlcv_callback(self, exchange: str, exchange_id: str, cryptocurrency: str, symbol: str,
                             time_frame: str, candle: dict):
        with self.trading_mode_trigger():
            await self.call_script(self.matrix_id, cryptocurrency, symbol, time_frame,
                                   commons_enums.ActivationTopics.FULL_CANDLES.value,
                                   candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value],
                                   candle=candle)

    async def kline_callback(self, exchange: str, exchange_id: str, cryptocurrency: str, symbol: str,
                             time_frame, kline: dict):
        with self.trading_mode_trigger():
            await self.call_script(self.matrix_id, cryptocurrency, symbol, time_frame,
                                   commons_enums.ActivationTopics.IN_CONSTRUCTION_CANDLES.value,
                                   kline[commons_enums.PriceIndexes.IND_PRICE_TIME.value],
                                   kline=kline)

    async def set_final_eval(self, matrix_id: str, cryptocurrency: str, symbol: str, time_frame):
        await self.call_script(matrix_id, cryptocurrency, symbol, time_frame,
                               commons_enums.ActivationTopics.EVALUATORS.value,
                               self._get_latest_eval_time(matrix_id, cryptocurrency, symbol, time_frame))

    def _get_latest_eval_time(self, matrix_id: str, cryptocurrency: str, symbol: str, time_frame):
        try:
            import octobot_evaluators.matrix as matrix
            import octobot_evaluators.enums as evaluators_enums
            return matrix.get_latest_eval_time(matrix_id,
                                               exchange_name=self.exchange_name,
                                               tentacle_type=evaluators_enums.EvaluatorMatrixTypes.SCRIPTED.value,
                                               cryptocurrency=cryptocurrency,
                                               symbol=symbol,
                                               time_frame=time_frame)
        except ImportError:
            self.logger.error("OctoBot-Evaluators is required for a matrix callback")
            return None

    async def call_script(self, matrix_id: str, cryptocurrency: str, symbol: str, time_frame: str,
                          trigger_source: str, trigger_cache_timestamp: float,
                          candle: dict = None, kline: dict = None, init_call: bool = False):
        context = self.get_context(matrix_id, cryptocurrency, symbol, time_frame, trigger_source,
                                   trigger_cache_timestamp, candle, kline, init_call)
        self.last_call_by_timeframe[time_frame] = \
            (matrix_id, cryptocurrency, symbol, time_frame, trigger_source, trigger_cache_timestamp, candle, kline, init_call)
        context.matrix_id = matrix_id
        context.cryptocurrency = cryptocurrency
        context.symbol = symbol
        context.time_frame = time_frame
        initialized = True
        try:
            if not self.run_data_writer.are_data_initialized and not \
                    self.trading_mode.__class__.INITIALIZED_DB_BY_BOT_ID.get(self.trading_mode.bot_id, False):
                await self._reset_run_data(context)
            await self.trading_mode.get_script(live=True)(context)
        except errors.UnreachableExchange:
            raise
        except (commons_errors.MissingDataError, commons_errors.ExecutionAborted) as e:
            self.logger.debug(f"Script execution aborted: {e}")
            initialized = self.run_data_writer.are_data_initialized
        except Exception as e:
            self.logger.exception(e, True, f"Error when running script: {e}")
        finally:
            if not self.exchange_manager.is_backtesting:
                # update db after each run only in live mode
                for writer in self.writers():
                    await writer.flush()
                if context.has_cache(context.symbol, context.time_frame):
                    await context.get_cache().flush()
            self.run_data_writer.set_initialized_flags(initialized)
            self.symbol_writer.set_initialized_flags(initialized, (time_frame,))

    def get_context(self, matrix_id, cryptocurrency, symbol, time_frame, trigger_source, trigger_cache_timestamp,
                    candle, kline, init_call=False):
        context = context_management.Context(
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
            self.run_data_writer,
            self.orders_writer,
            self.trades_writer,
            self.transactions_writer,
            self.symbol_writer,
            self.trading_mode,
            trigger_cache_timestamp,
            trigger_source,
            candle or kline,
            None,
            None,
        )
        context.enable_trading = not init_call
        return context

    async def _reset_run_data(self, context):
        await basic_keywords.clear_run_data(self.run_data_writer)
        await basic_keywords.save_metadata(self.run_data_writer, await self.get_live_metadata())
        await basic_keywords.save_portfolio(self.run_data_writer, context)
        self.trading_mode.__class__.INITIALIZED_DB_BY_BOT_ID[self.trading_mode.bot_id] = True

    async def init_user_inputs(self, should_clear_inputs):
        if should_clear_inputs:
            await basic_keywords.clear_user_inputs(self.run_data_writer)
        await self._register_required_user_inputs(
            self.get_context(None, None, self.trading_mode.symbol, None, None, None, None, None, True))

    async def _register_required_user_inputs(self, context):
        if context.exchange_manager.is_future:
            await basic_keywords.user_select_leverage(context)

        # register activating topics user input
        activation_topic_values = [
            commons_enums.ActivationTopics.EVALUATORS.value,
            commons_enums.ActivationTopics.FULL_CANDLES.value,
            commons_enums.ActivationTopics.IN_CONSTRUCTION_CANDLES.value
        ]
        await basic_keywords.user_input(context, commons_constants.CONFIG_ACTIVATION_TOPICS, "options",
                                        commons_enums.ActivationTopics.EVALUATORS.value,
                                        options=activation_topic_values,
                                        show_in_optimizer=False, show_in_summary=False, order=1000)

    @contextlib.asynccontextmanager
    async def get_metadata_writer(self, with_lock):
        async with databases.DBWriter.database(self.database_manager.get_backtesting_metadata_identifier(),
                                               with_lock=with_lock) as writer:
            yield writer

    async def _save_transactions(self):
        await basic_keywords.store_transactions(
            None,
            self.exchange_manager.exchange_personal_data.transactions_manager.transactions.values(),
            chart=None,
            writer=self.transactions_writer
        )

    async def stop(self) -> None:
        """
        Stop trading mode channels subscriptions
        """
        if not self.are_metadata_saved and self.exchange_manager is not None and self.exchange_manager.is_backtesting:
            await self.run_data_writer.flush()
            user_inputs = await basic_keywords.get_user_inputs(self.run_data_writer)
            await self._save_transactions()
            await asyncio.gather(*(self.trading_mode.close_writer(writer.get_db_path()) for writer in self.writers()))
            if not self.trading_mode.__class__.SAVED_RUN_METADATA_DB_BY_BOT_ID.get(self.trading_mode.bot_id, False):
                try:
                    self.trading_mode.__class__.SAVED_RUN_METADATA_DB_BY_BOT_ID[self.trading_mode.bot_id] = True
                    async with self.get_metadata_writer(with_lock=True) as writer:
                        await basic_keywords.save_metadata(writer, await self.get_backtesting_metadata(user_inputs))
                        self.are_metadata_saved = True
                except Exception:
                    self.trading_mode.__class__.SAVED_RUN_METADATA_DB_BY_BOT_ID[self.trading_mode.bot_id] = False
                    raise
        await super().stop()
