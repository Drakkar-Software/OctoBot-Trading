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
import async_channel.channels as channels
import octobot_trading.exchange_channel as exchanges_channel
import octobot_trading.api as trading_api
import octobot_trading.modes.abstract_trading_mode as abstract_trading_mode
import octobot_trading.modes.channel as modes_channel
import octobot_trading.modes.script_keywords.context_management as context_management
import octobot_trading.modes.script_keywords.basic_keywords as basic_keywords
import octobot_trading.constants as trading_constants
import octobot_trading.enums as trading_enums
import octobot_trading.errors as errors
import octobot_trading.storage as storage
import octobot_trading.personal_data as personal_data
import octobot_backtesting.api as backtesting_api
import octobot_tentacles_manager.api as tentacles_manager_api


class AbstractScriptedTradingMode(abstract_trading_mode.AbstractTradingMode):
    TRADING_SCRIPT_MODULE = None
    BACKTESTING_SCRIPT_MODULE = None

    BACKTESTING_ID_BY_BOT_ID = {}
    INITIALIZED_DB_BY_BOT_ID = {}
    SAVED_RUN_METADATA_DB_BY_BOT_ID = {}
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
            db = storage.RunDatabasesProvider.instance().get_trades_db(self.bot_id, self.exchange_manager.exchange_name)
            await basic_keywords.store_trade(None, trade, exchange_manager=self.exchange_manager, writer=db)

    async def _user_commands_callback(self, bot_id, subject, action, data) -> None:
        self.logger.debug(f"Received {action} command.")
        if action == commons_enums.UserCommands.RELOAD_SCRIPT.value:
            await self.reload_script(live=True)
            await self.reload_script(live=False)
        elif action == commons_enums.UserCommands.CLEAR_PLOTTING_CACHE.value:
            await self.clear_plotting_cache()
        elif action == commons_enums.UserCommands.CLEAR_SIMULATED_ORDERS_CACHE.value:
            await self.clear_simulated_orders_cache()
        elif action == commons_enums.UserCommands.CLEAR_SIMULATED_TRADES_CACHE.value:
            await self.clear_simulated_trades_cache()
        elif action == commons_enums.UserCommands.CLEAR_SIMULATED_TRANSACTIONS_CACHE.value:
            await self.clear_simulated_transactions_cache()

    async def clear_simulated_orders_cache(self):
        await basic_keywords.clear_orders_cache(
            storage.RunDatabasesProvider.instance().get_orders_db(self.bot_id, self.exchange_manager.exchange_name)
        )

    async def clear_simulated_trades_cache(self):
        await basic_keywords.clear_trades_cache(
            storage.RunDatabasesProvider.instance().get_trades_db(self.bot_id, self.exchange_manager.exchange_name)
        )

    async def clear_simulated_transactions_cache(self):
        await basic_keywords.clear_trades_cache(
            storage.RunDatabasesProvider.instance().get_transactions_db(self.bot_id, self.exchange_manager.exchange_name)
        )

    async def clear_plotting_cache(self):
        await basic_keywords.clear_all_tables(
            storage.RunDatabasesProvider.instance().get_symbol_db(self.bot_id,
                                                                  self.exchange_manager.exchange_name,
                                                                  self.symbol)
        )

    @classmethod
    async def get_backtesting_plot(cls, exchange, symbol, backtesting_id, optimizer_id, optimization_campaign):
        ctx = context_management.Context.minimal(cls, logging.get_logger(cls.get_name()), exchange, symbol,
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
        symbol_db = storage.RunDatabasesProvider.instance().get_symbol_db(self.bot_id,
                                                                          self.exchange_manager.exchange_name,
                                                                          self.symbol)
        symbol_db.set_initialized_flags(False)
        for producer in self.producers:
            for time_frame, call_args in producer.last_call_by_timeframe.items():
                run_db = storage.RunDatabasesProvider.instance().get_run_db(self.bot_id)
                await basic_keywords.clear_user_inputs(run_db)
                await producer.init_user_inputs(False)
                run_db.set_initialized_flags(False, (time_frame, ))
                self.__class__.INITIALIZED_DB_BY_BOT_ID[self.bot_id] = False
                await databases.CacheManager().close_cache(commons_constants.UNPROVIDED_CACHE_IDENTIFIER,
                                                           reset_cache_db_ids=True)
                await producer.call_script(*call_args)

    @classmethod
    async def get_backtesting_id(cls, bot_id):
        try:
            return cls.BACKTESTING_ID_BY_BOT_ID[bot_id]
        except KeyError:
            raise RuntimeError(f"No backtesting id for bot_id: {bot_id}")

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
        draw_down = round(float(trading_api.get_draw_down(self.exchange_manager)), 3)
        r_sq_end_balance \
            = await trading_api.get_coefficient_of_determination(self.exchange_manager,
                                                                 use_high_instead_of_end_balance=False)
        r_sq_max_balance = await trading_api.get_coefficient_of_determination(self.exchange_manager)

        return {
            commons_enums.BacktestingMetadata.OPTIMIZATION_CAMPAIGN.value:
                self.run_dbs_identifier.optimization_campaign_name,
            commons_enums.BacktestingMetadata.ID.value: self.run_dbs_identifier.backtesting_id,
            commons_enums.BacktestingMetadata.GAINS.value: round(float(profitability), 8),
            commons_enums.BacktestingMetadata.PERCENT_GAINS.value: round(float(profitability_percent), 3),
            commons_enums.BacktestingMetadata.END_PORTFOLIO.value: str(end_portfolio),
            commons_enums.BacktestingMetadata.START_PORTFOLIO.value: str(origin_portfolio),
            commons_enums.BacktestingMetadata.WIN_RATE.value: win_rate,
            commons_enums.BacktestingMetadata.DRAW_DOWN.value: draw_down or 0,
            commons_enums.BacktestingMetadata.COEFFICIENT_OF_DETERMINATION_MAX_BALANCE.value: r_sq_max_balance or 0,
            commons_enums.BacktestingMetadata.COEFFICIENT_OF_DETERMINATION_END_BALANCE.value: r_sq_end_balance or 0,
            commons_enums.BacktestingMetadata.SYMBOLS.value: symbols,
            commons_enums.BacktestingMetadata.TIME_FRAMES.value: time_frames,
            commons_enums.BacktestingMetadata.START_TIME.value: backtesting_api.get_backtesting_starting_time(
                self.exchange_manager.exchange.backtesting),
            commons_enums.BacktestingMetadata.END_TIME.value: backtesting_api.get_backtesting_ending_time(
                self.exchange_manager.exchange.backtesting),
            commons_enums.BacktestingMetadata.DURATION.value: round(backtesting_api.get_backtesting_duration(
                self.exchange_manager.exchange.backtesting), 3),
            commons_enums.BacktestingMetadata.ENTRIES.value: len(entries),
            commons_enums.BacktestingMetadata.WINS.value: wins,
            commons_enums.BacktestingMetadata.LOSES.value: len(entries) - wins,
            commons_enums.BacktestingMetadata.TRADES.value: len(trades),
            commons_enums.BacktestingMetadata.TIMESTAMP.value: self.trading_mode.timestamp,
            commons_enums.BacktestingMetadata.NAME.value: self.trading_mode.script_name,
            commons_enums.BacktestingMetadata.LEVERAGE.value: leverage,
            commons_enums.BacktestingMetadata.USER_INPUTS.value: formatted_user_inputs,
            commons_enums.BacktestingMetadata.BACKTESTING_FILES.value: trading_api.get_backtesting_data_files(
                self.exchange_manager),
            commons_enums.BacktestingMetadata.EXCHANGE.value: self.exchange_name
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
            commons_enums.DBRows.REFERENCE_MARKET.value: trading_api.get_reference_market(self.config),
            commons_enums.DBRows.START_TIME.value: start_time,
            commons_enums.DBRows.END_TIME.value: end_time,
            commons_enums.DBRows.TRADING_TYPE.value: exchange_type,
            commons_enums.DBRows.EXCHANGES.value: exchanges,
            commons_enums.DBRows.FUTURE_CONTRACTS.value: future_contracts_by_exchange,
            commons_enums.DBRows.SYMBOLS.value: self.exchange_manager.exchange_config.traded_symbol_pairs,
        }

    def __init__(self, channel, config, trading_mode, exchange_manager):
        super().__init__(channel, config, trading_mode, exchange_manager)
        self.last_call_by_timeframe = {}
        self.traded_pair = trading_mode.symbol
        self.are_metadata_saved = False

    async def start(self) -> None:
        await super().start()

        self.run_dbs_identifier = storage.RunDatabasesProvider.instance().get_run_databases_identifier(
            self.trading_mode.bot_id
        )
        # register backtesting id
        self.trading_mode.__class__.BACKTESTING_ID_BY_BOT_ID[self.trading_mode.bot_id] = \
            self.run_dbs_identifier.backtesting_id
        await self.run_dbs_identifier.initialize(self.exchange_name)
        # refresh user inputs
        await self.init_user_inputs(True)
        if not self.exchange_manager.is_backtesting:
            asyncio.create_task(self._schedule_initialization_call())

    async def _schedule_initialization_call(self):
        # initialization call is a special call that does not trigger trades and allows the script
        # to be run at least once in order to initialize its configuration
        if self.exchange_manager.is_backtesting:
            # not necessary in backtesting
            return

        # fake an full candle call
        cryptocurrency, symbol, time_frame = self._get_initialization_call_args()
        # wait for symbol data to be initialized
        # TODO use trading ready event when done
        candle = await self._wait_for_symbol_init(symbol, time_frame, 30)
        if candle is None:
            self.logger.error(f"Can't initialize trading script: {symbol} {time_frame} candles are not fetched")
        await self.ohlcv_callback(self.exchange_name, self.exchange_manager.id, cryptocurrency, symbol, time_frame,
                                  candle, init_call=True)

    async def _wait_for_symbol_init(self, symbol, time_frame, timeout):
        # warning: should never be called in backtesting
        tf = commons_enums.TimeFrames(time_frame)
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                if self.exchange_manager.is_future:
                    # wait for contracts to be loaded
                    _ = self.exchange_manager.exchange.pair_contracts[symbol]
                candles_manager = self.exchange_manager.exchange_symbols_data.get_exchange_symbol_data(
                    symbol,
                    allow_creation=False) \
                    .symbol_candles[tf]
                candle_data = candles_manager.get_candles(5)
                current_time = self.exchange_manager.exchange.get_exchange_current_time()
                time_frame_sec = commons_enums.TimeFramesMinutes[tf] * commons_constants.MINUTE_TO_SECONDS
                last_full_candle_time = current_time - current_time % time_frame_sec - time_frame_sec
                for candle in reversed(candle_data):
                    if candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value] == last_full_candle_time:
                        return candle
                # return the candle right before the last (last being in construction)
                return candle_data[-2]
            except KeyError:
                # no symbol data initialized, keep waiting
                await asyncio.sleep(0.2)
        return None

    def _get_initialization_call_args(self):
        currency = next(iter(self.exchange_manager.exchange_config.traded_cryptocurrencies))
        symbol = self.exchange_manager.exchange_config.traded_cryptocurrencies[currency][0]
        time_frame = self.exchange_manager.exchange_config.traded_time_frames[0]
        return currency, symbol, time_frame.value

    async def ohlcv_callback(self, exchange: str, exchange_id: str, cryptocurrency: str, symbol: str,
                             time_frame: str, candle: dict, init_call: bool = False):
        with self.trading_mode_trigger():
            # add a full candle to time to get the real time
            trigger_time = candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value] + \
                           commons_enums.TimeFramesMinutes[commons_enums.TimeFrames(time_frame)] * \
                           commons_constants.MINUTE_TO_SECONDS
            await self.call_script(self.matrix_id, cryptocurrency, symbol, time_frame,
                                   commons_enums.ActivationTopics.FULL_CANDLES.value,
                                   trigger_time,
                                   candle=candle,
                                   init_call=init_call)

    async def kline_callback(self, exchange: str, exchange_id: str, cryptocurrency: str, symbol: str,
                             time_frame, kline: dict):
        with self.trading_mode_trigger():
            await self.call_script(self.matrix_id, cryptocurrency, symbol, time_frame,
                                   commons_enums.ActivationTopics.IN_CONSTRUCTION_CANDLES.value,
                                   kline[commons_enums.PriceIndexes.IND_PRICE_TIME.value],
                                   kline=kline)

    async def set_final_eval(self, matrix_id: str, cryptocurrency: str, symbol: str, time_frame):
        await self.call_script(matrix_id, cryptocurrency, symbol, time_frame,
                               commons_enums.ActivationTopics.EVALUATION_CYCLE.value,
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
        run_data_writer = storage.RunDatabasesProvider.instance().get_run_db(self.trading_mode.bot_id)
        try:
            if not run_data_writer.are_data_initialized and not \
                    self.trading_mode.__class__.INITIALIZED_DB_BY_BOT_ID.get(self.trading_mode.bot_id, False):
                await self._reset_run_data(context)
            await self._pre_script_call(context)
            await self.trading_mode.get_script(live=True)(context)
        except errors.UnreachableExchange:
            raise
        except (commons_errors.MissingDataError, commons_errors.ExecutionAborted) as e:
            self.logger.debug(f"Script execution aborted: {e}")
            initialized = run_data_writer.are_data_initialized
        except Exception as e:
            self.logger.exception(e, True, f"Error when running script: {e}")
        finally:
            if not self.exchange_manager.is_backtesting:
                # update db after each run only in live mode
                for database in self.all_databases().values():
                    if database:
                        await database.flush()
                if context.has_cache(context.symbol, context.time_frame):
                    await context.get_cache().flush()
            run_data_writer.set_initialized_flags(initialized)
            storage.RunDatabasesProvider.instance().get_symbol_db(self.trading_mode.bot_id,
                                                                  self.exchange_name, symbol)\
                .set_initialized_flags(initialized, (time_frame,))

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
            self.trading_mode.__class__,
            trigger_cache_timestamp,
            trigger_source,
            candle or kline,
            None,
            None,
        )
        context.enable_trading = not init_call
        return context

    async def _reset_run_data(self, context):
        run_data_writer = storage.RunDatabasesProvider.instance().get_run_db(self.trading_mode.bot_id)
        await basic_keywords.clear_run_data(run_data_writer)
        await basic_keywords.save_metadata(run_data_writer, await self.get_live_metadata())
        await basic_keywords.save_portfolio(run_data_writer, context)
        self.trading_mode.__class__.INITIALIZED_DB_BY_BOT_ID[self.trading_mode.bot_id] = True

    async def init_user_inputs(self, should_clear_inputs):
        if should_clear_inputs:
            await basic_keywords.clear_user_inputs(
                storage.RunDatabasesProvider.instance().get_run_db(self.trading_mode.bot_id)
            )
        await self._register_required_user_inputs(
            self.get_context(None, None, self.trading_mode.symbol, None, None, None, None, None, True))

    async def _pre_script_call(self, context):
        await basic_keywords.set_leverage(context, await basic_keywords.user_select_leverage(context))

    async def _register_required_user_inputs(self, context):
        if context.exchange_manager.is_future:
            await basic_keywords.user_select_leverage(context)

        # register activating topics user input
        activation_topic_values = [
            commons_enums.ActivationTopics.EVALUATION_CYCLE.value,
            commons_enums.ActivationTopics.FULL_CANDLES.value,
            commons_enums.ActivationTopics.IN_CONSTRUCTION_CANDLES.value
        ]
        await basic_keywords.get_activation_topics(
            context,
            commons_enums.ActivationTopics.EVALUATION_CYCLE.value,
            activation_topic_values
        )

    @contextlib.asynccontextmanager
    async def get_metadata_writer(self, with_lock):
        async with databases.DBWriter.database(self.run_dbs_identifier.get_backtesting_metadata_identifier(),
                                               with_lock=with_lock) as writer:
            yield writer

    async def _save_transactions(self):
        await basic_keywords.store_transactions(
            None,
            self.exchange_manager.exchange_personal_data.transactions_manager.transactions.values(),
            writer=storage.RunDatabasesProvider.instance().get_transactions_db(self.trading_mode.bot_id,
                                                                               self.exchange_name)
        )

    async def stop(self) -> None:
        """
        Stop trading mode channels subscriptions
        """
        if not self.are_metadata_saved and self.exchange_manager is not None and self.exchange_manager.is_backtesting:
            run_data_writer = storage.RunDatabasesProvider.instance().get_run_db(self.trading_mode.bot_id)
            await run_data_writer.flush()
            user_inputs = await basic_keywords.get_user_inputs(run_data_writer)
            await self._save_transactions()
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
