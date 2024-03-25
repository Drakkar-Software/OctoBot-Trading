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
import contextlib
import asyncio
import concurrent.futures

import async_channel.enums as channel_enums

import octobot_commons.channels_name as channels_name
import octobot_commons.constants as common_constants
import octobot_commons.enums as common_enums
import octobot_commons.logging as logging
import octobot_commons.databases as databases
import octobot_commons.configuration as commons_configuration
import octobot_commons.asyncio_tools as asyncio_tools

import octobot_trading.enums as enums
import octobot_trading.constants as constants
import octobot_trading.errors as errors
import octobot_trading.util as util
import octobot_trading.exchanges.exchanges as exchanges
import octobot_trading.exchange_channel as exchanges_channel
import octobot_trading.modes.channel as modes_channel
import octobot_trading.modes.script_keywords as script_keywords
import octobot_trading.modes.mode_activity as mode_activity
import octobot_trading.storage.util as storage_util


class AbstractTradingModeProducer(modes_channel.ModeChannelProducer):
    TOPIC_TO_CHANNEL_NAME = {
        common_enums.ActivationTopics.FULL_CANDLES.value:
            channels_name.OctoBotTradingChannelsName.OHLCV_CHANNEL.value,
        common_enums.ActivationTopics.IN_CONSTRUCTION_CANDLES.value:
            channels_name.OctoBotTradingChannelsName.KLINE_CHANNEL.value,
        common_enums.ActivationTopics.EVALUATION_CYCLE.value:
            channels_name.OctoBotEvaluatorsChannelsName.MATRIX_CHANNEL.value,
    }
    CONFIG_INIT_TIMEOUT = 1 * common_constants.MINUTE_TO_SECONDS    # let time for orders to be fetched before
    # declaring timeout at first trigger
    PRODUCER_LOCKS_BY_EXCHANGE_ID = {}  # use to identify exchange-wide actions

    def __init__(self, channel, config, trading_mode, exchange_manager):
        super().__init__(channel)
        # the trading mode instance logger
        self.logger = logging.get_logger(self.__class__.__name__)

        # the trading mode instance
        self.trading_mode = trading_mode

        # the global bot config
        self.config = config

        # the trading mode exchange manager
        self.exchange_manager = exchange_manager

        # shortcut
        self.exchange_name = self.exchange_manager.exchange_name

        # matrix_id shortcut
        self.matrix_id = None

        # the final eval used by TradingModeConsumers, default value is 0
        self.final_eval = constants.ZERO

        # the producer state used by TradingModeConsumers
        self.state = None

        # the consumer instances
        self.evaluator_consumers = []
        self.trading_consumers = []

        self.time_frame_filter = None

        # Define trading modes default consumer priority level
        self.priority_level: int = channel_enums.ChannelConsumerPriorityLevels.MEDIUM.value

        self.symbol = None

        self._is_ready_to_trade = None
        self.on_reload_config()

        # cleared (awaitable) when inside self.trading_mode_trigger
        self._is_trigger_completed = asyncio.Event()
        self._is_trigger_completed.set()

        self.last_activity: mode_activity.TradingModeActivity = mode_activity.TradingModeActivity()

    def on_reload_config(self):
        """
        Called at constructor and after the associated trading mode's reload_config.
        Implement if necessary
        """

    def is_cryptocurrency_wildcard(self):
        """
        Should be True only if self.trading_mode.get_is_cryptocurrency_wildcard() is already True
        But can overwritten (with return False) to disable wildcard trigger when get_is_cryptocurrency_wildcard() is True
        :return: True if the mode producer should be triggered by all cryptocurrencies
        """
        return self.trading_mode.get_is_cryptocurrency_wildcard()

    def is_symbol_wildcard(self):
        """
        Should be True only if self.trading_mode.get_is_symbol_wildcard() is already True
        But can overwritten (with return False) to disable wildcard trigger when get_is_symbol_wildcard() is True
        :return: True if the mode producer should be triggered by all symbols
        """
        return self.trading_mode.get_is_symbol_wildcard()

    def is_time_frame_wildcard(self):
        """
        Should be True only if self.trading_mode.get_is_time_frame_wildcard() is already True
        But can overwritten (with return False) to disable wildcard trigger when get_is_time_frame_wildcard() is True
        :return: True if the mode producer should be triggered by all timeframes
        """
        return self.trading_mode.get_is_time_frame_wildcard()

    # noinspection PyArgumentList
    async def start(self) -> None:
        self._is_ready_to_trade = self._is_ready_to_trade or asyncio.Event()
        try:
            await self.inner_start()
        finally:
            self.logger.debug(
                f"Ready to trade on {self.exchange_manager.exchange_name}, symbol: {self.trading_mode.symbol}"
            )
            self._is_ready_to_trade.set()

    def force_is_ready_to_trade(self):
        if self._is_ready_to_trade is None:
            self._is_ready_to_trade = asyncio.Event()
        self._is_ready_to_trade.set()

    def unset_is_ready_to_trade(self):
        if self._is_ready_to_trade is None:
            self._is_ready_to_trade = asyncio.Event()
        if self._is_ready_to_trade.is_set():
            self._is_ready_to_trade.clear()

    async def inner_start(self) -> None:
        """
        Start trading mode channels subscriptions
        """
        registration_topics = self.get_channels_registration()
        if registration_topics:
            trigger_time_frames = self.get_trigger_time_frames()
            currency_filter = self.trading_mode.cryptocurrency \
                if self.trading_mode.cryptocurrency is not None and not self.is_cryptocurrency_wildcard() \
                else common_constants.CONFIG_WILDCARD
            symbol_filter = self.trading_mode.symbol \
                if self.trading_mode.symbol is not None and not self.is_symbol_wildcard() \
                else common_constants.CONFIG_WILDCARD
            self.time_frame_filter = self.trading_mode.time_frame \
                if self.trading_mode.time_frame is not None and self.is_time_frame_wildcard() \
                else [tf.value
                      for tf in self.exchange_manager.exchange_config.get_relevant_time_frames()
                      if tf.value in trigger_time_frames or
                      trigger_time_frames == common_constants.CONFIG_WILDCARD]
            if trigger_time_frames != common_constants.CONFIG_WILDCARD and \
               len(self.time_frame_filter) < len(trigger_time_frames):
                missing_time_frames = [tf for tf in trigger_time_frames if tf not in self.time_frame_filter]
                self.logger.error(f"Missing timeframe to satisfy {trigger_time_frames} required time frames. "
                                  f"Please activate those timeframes {missing_time_frames}")
            self.matrix_id = exchanges.Exchanges.instance().get_exchange(self.exchange_manager.exchange_name,
                                                                         self.exchange_manager.id).matrix_id
            await self._subscribe_to_registration_topic(registration_topics, currency_filter, symbol_filter)
        await self.init_user_inputs(False)
        await self._wait_for_bot_init(self.CONFIG_INIT_TIMEOUT)

    async def _subscribe_to_registration_topic(self, registration_topics, currency_filter, symbol_filter):
        for registration_topic in registration_topics:
            if registration_topic == channels_name.OctoBotEvaluatorsChannelsName.MATRIX_CHANNEL.value:
                # register to matrix channel if necessary
                try:
                    import octobot_evaluators.evaluators.channel as evaluators_channel
                    import octobot_evaluators.enums as evaluators_enums
                    consumer = await evaluators_channel.get_chan(registration_topic, self.matrix_id).new_consumer(
                        callback=self.get_callback(registration_topic),
                        priority_level=self.priority_level,
                        matrix_id=self.matrix_id,
                        cryptocurrency=currency_filter,
                        symbol=symbol_filter,
                        evaluator_type=evaluators_enums.EvaluatorMatrixTypes.STRATEGIES.value,
                        exchange_name=self.exchange_name,
                        # no time_frame filter to allow receiving updates from strategies without timeframes in wildcard
                        time_frame=common_constants.CONFIG_WILDCARD if self.is_time_frame_wildcard()
                        else self.time_frame_filter,
                        supervised=self.exchange_manager.is_backtesting
                    )
                    self.evaluator_consumers.append(
                        (consumer, registration_topic)
                    )
                    self.trading_mode.is_triggered_after_candle_close = False
                except (KeyError, ImportError):
                    self.logger.error(f"Can't connect matrix channel on {self.exchange_name}")
            else:
                # register to trading channels if necessary
                consumer = await exchanges_channel.get_chan(registration_topic, self.exchange_manager.id).new_consumer(
                    callback=self.get_callback(registration_topic),
                    priority_level=self.priority_level,
                    cryptocurrency=currency_filter,
                    symbol=symbol_filter,
                    time_frame=self.time_frame_filter
                )
                self.trading_consumers.append(
                    (consumer, registration_topic)
                )
                if registration_topic == channels_name.OctoBotTradingChannelsName.OHLCV_CHANNEL.value:
                    self.trading_mode.is_triggered_after_candle_close = True

    def get_callback(self, chan_name):
        return {
            channels_name.OctoBotTradingChannelsName.OHLCV_CHANNEL.value: self.ohlcv_callback,
            channels_name.OctoBotTradingChannelsName.KLINE_CHANNEL.value: self.kline_callback,
            channels_name.OctoBotEvaluatorsChannelsName.MATRIX_CHANNEL.value: self.matrix_callback,
        }[chan_name]

    def get_channels_registration(self):
        registration_channels = []
        # Activate on evaluation cycle only by default
        topic = self.trading_mode.trading_config.get(common_constants.CONFIG_ACTIVATION_TOPICS.replace(" ", "_"),
                                                     common_enums.ActivationTopics.EVALUATION_CYCLE.value)
        try:
            registration_channels.append(self.TOPIC_TO_CHANNEL_NAME[topic])
        except KeyError:
            self.logger.error(f"Unknown registration topic: {topic}")
        return registration_channels

    def get_trigger_time_frames(self):
        return self.trading_mode.trading_config.get(common_constants.CONFIG_TRIGGER_TIMEFRAMES,
                                                    common_constants.CONFIG_WILDCARD)

    async def stop(self) -> None:
        """
        Stop trading mode channels subscriptions
        """
        await super().stop()
        if self.exchange_manager is not None:
            for consumer, channel_name in self.evaluator_consumers:
                try:
                    import octobot_evaluators.evaluators.channel as evaluators_channel
                    await evaluators_channel.get_chan(channel_name,
                                                      exchanges.Exchanges.instance().get_exchange(
                                                          self.exchange_manager.exchange_name,
                                                          self.exchange_manager.id).matrix_id
                                                      ).remove_consumer(consumer)
                except (KeyError, ImportError):
                    self.logger.error(f"Can't unregister {channel_name} channel on {self.exchange_name}")
            for consumer, channel_name in self.trading_consumers:
                try:
                    await exchanges_channel.get_chan(channel_name, self.exchange_manager.id).remove_consumer(consumer)
                except (KeyError, ImportError):
                    self.logger.error(f"Can't unregister {channel_name} channel on {self.exchange_name}")
            self.delete_producer_exchange_wide_lock(self.exchange_manager)
        self.flush()

    def flush(self) -> None:
        """
        Flush all instance objects reference
        """
        self.trading_mode = None
        self.exchange_manager = None
        self.evaluator_consumers = []
        self.trading_consumers = []

    async def ohlcv_callback(self, exchange: str, exchange_id: str, cryptocurrency: str, symbol: str,
                             time_frame: str, candle: dict):
        self.logger.error(f"ohlcv_callback is registered but not implemented")

    async def kline_callback(self, exchange: str, exchange_id: str, cryptocurrency: str, symbol: str,
                             time_frame, kline: dict):
        self.logger.error(f"kline_callback is registered but not implemented")

    async def matrix_callback(self, matrix_id, evaluator_name, evaluator_type,
                              eval_note, eval_note_type, exchange_name, cryptocurrency, symbol, time_frame) -> None:
        """
        Called when a strategy updates the matrix
        :param matrix_id: the matrix_id
        :param evaluator_name: the evaluator name, should be the strategy name
        :param evaluator_type: the evaluator type, should be EvaluatorMatrixTypes.STRATEGIES.value
        :param eval_note: the eval note, should be the strategy eval note
        :param eval_note_type: the eval note type
        :param exchange_name: the exchange name
        :param cryptocurrency: the cryptocurrency
        :param symbol: the symbol
        :param time_frame: the time frame
        """
        if time_frame is None or time_frame in self.time_frame_filter:
            await self.finalize(exchange_name=exchange_name, matrix_id=matrix_id, cryptocurrency=cryptocurrency,
                                symbol=symbol, time_frame=time_frame,
                                trigger_source=common_enums.TriggerSource.EVALUATION_MATRIX.value)

    async def finalize(self, exchange_name: str,
                       matrix_id: str,
                       cryptocurrency: str = None,
                       symbol: str = None,
                       time_frame=None,
                       trigger_source: str = common_enums.TriggerSource.UNDEFINED.value
                       ) -> None:
        """
        Finalize evaluation
        """
        if exchange_name != self.exchange_name or not self.exchange_manager.trader.is_enabled:
            # Do nothing if not its exchange
            return
        await self.trigger(matrix_id, cryptocurrency, symbol, time_frame, trigger_source)

    async def trigger(self, matrix_id: str = None, cryptocurrency: str = None, symbol: str = None, time_frame=None,
                      trigger_source: str = common_enums.TriggerSource.UNDEFINED.value) -> None:
        """
        Called by finalize and MANUAL_TRIGGER user command. Override if necessary
        """
        try:
            async with self.trading_mode_trigger(), self.trading_mode.remote_signal_publisher(symbol):
                await self.set_final_eval(matrix_id=matrix_id,
                                          cryptocurrency=cryptocurrency,
                                          symbol=symbol,
                                          time_frame=time_frame,
                                          trigger_source=trigger_source)
        except errors.InitializingError as e:
            self.logger.exception(
                e,
                True,
                f"Ignored signal: exchange: {self.exchange_manager.exchange_name} symbol: {symbol}, "
                f"time_frame: {time_frame}. "
                f"Trading mode is not yet ready to trade, OctoBot is still initializing and fetching required data."
            )

    async def wait_for_trigger_completion(self, timeout):
        if self._is_trigger_completed.is_set():
            return
        await asyncio.wait_for(self._is_trigger_completed.wait(), timeout=timeout)

    @contextlib.asynccontextmanager
    async def trading_mode_trigger(self, skip_health_check=False):
        try:
            self._is_trigger_completed.clear()
            if not self._is_ready_to_trade.is_set():
                if self.exchange_manager.is_backtesting:
                    raise asyncio.TimeoutError(f"Trading mode producer has to be started in backtesting")
                self.logger.debug("Waiting for orders initialization to proceed")
                try:
                    await asyncio.wait_for(self._is_ready_to_trade.wait(), self.CONFIG_INIT_TIMEOUT)
                except asyncio.TimeoutError as e:
                    raise errors.InitializingError() from e
                self.logger.debug("Order initialized")
            if self.trading_mode.is_health_check_required() and not skip_health_check:
                await self.trading_mode.health_check([], {})
            yield
        except errors.InitializingError:
            raise
        except errors.UnreachableExchange as e:
            self.logger.warning(f"Error when calling trading mode: {e}")
        except AttributeError:
            if self._is_ready_to_trade is None:
                raise AttributeError(f"{self.__class__.__name__} has to be started. self._is_ready_to_trade is None")
            raise
        except Exception as e:
            self.logger.exception(e, True, f"Error when calling trading mode: {e}")
        finally:
            self._is_trigger_completed.set()
            await self.post_trigger()

    async def post_trigger(self):
        pass

    async def set_final_eval(self, matrix_id: str, cryptocurrency: str, symbol: str, time_frame,
                             trigger_source: str) -> None:
        """
        Called to calculate the final note or state => when any notification appears
        """
        raise NotImplementedError("set_final_eval not implemented")

    async def submit_trading_evaluation(self, cryptocurrency, symbol, time_frame,
                                        final_note=constants.ZERO,
                                        state=enums.EvaluatorStates.NEUTRAL,
                                        data=None) -> None:
        await self.send(trading_mode_name=self.trading_mode.get_name(),
                        cryptocurrency=cryptocurrency,
                        symbol=symbol,
                        time_frame=time_frame,
                        final_note=final_note,
                        state=state.value,
                        data=data if data is not None else {})

    @classmethod
    def get_should_cancel_loaded_orders(cls) -> bool:
        """
        Called by cancel_symbol_open_orders => return true if OctoBot should cancel all orders for a symbol including
        orders already existing when OctoBot started up
        """
        raise NotImplementedError("get_should_cancel_loaded_orders not implemented")

    async def cancel_symbol_open_orders(self, symbol, side=None, tag=None, exchange_order_ids=None) -> bool:
        """
        Cancel all symbol open orders
        """
        cancel_loaded_orders = self.get_should_cancel_loaded_orders()
        cancelled = False
        failed_to_cancel = False
        if self.exchange_manager.trader.is_enabled:
            for order in self.exchange_manager.exchange_personal_data.orders_manager.get_open_orders(
                symbol=symbol, tag=tag
            ):
                if (
                    not (order.is_cancelled() or order.is_closed())
                    and (cancel_loaded_orders or order.is_from_this_octobot)
                    and (side is None or (side is order.side))
                    and (exchange_order_ids is None or (order.exchange_order_id in exchange_order_ids))
                ):
                    if await self.trading_mode.cancel_order(order):
                        cancelled = True
                    else:
                        failed_to_cancel = True
        return cancelled and not failed_to_cancel

    def all_databases(self):
        provider = databases.RunDatabasesProvider.instance()
        account_type = storage_util.get_account_type_suffix_from_exchange_manager(self.exchange_manager)
        return {
            common_enums.RunDatabases.RUN_DATA_DB.value: provider.get_run_db(self.trading_mode.bot_id),
            common_enums.RunDatabases.ORDERS_DB.value:
                provider.get_orders_db(self.trading_mode.bot_id, account_type, self.exchange_name),
            common_enums.RunDatabases.TRADES_DB.value:
                provider.get_trades_db(self.trading_mode.bot_id, account_type, self.exchange_name),
            common_enums.RunDatabases.TRANSACTIONS_DB.value:
                provider.get_transactions_db(self.trading_mode.bot_id, account_type, self.exchange_name),
            self.trading_mode.symbol:
                provider.get_symbol_db(self.trading_mode.bot_id, self.exchange_name, self.trading_mode.symbol)
                if self.trading_mode.symbol else None,
        }

    async def _wait_for_symbol_init(self, symbol, time_frame, timeout) -> bool:
        try:
            await util.wait_for_topic_init(self.exchange_manager, timeout,
                                           common_enums.InitializationEventExchangeTopics.CANDLES.value, symbol)
            if self.exchange_manager.is_future:
                await util.wait_for_topic_init(self.exchange_manager, timeout,
                                               common_enums.InitializationEventExchangeTopics.CONTRACTS.value, symbol)
            return True
        except (asyncio.TimeoutError, concurrent.futures.TimeoutError):
            self.logger.error(f"Initialization took more than {timeout} seconds")
        return False

    async def _wait_for_bot_init(self, timeout, extra_topics: list=None) -> bool:
        try:
            topics = [
                common_enums.InitializationEventExchangeTopics.BALANCE.value,
                common_enums.InitializationEventExchangeTopics.ORDERS.value
            ] + (extra_topics if extra_topics else [])
            if self.trading_mode.REQUIRE_TRADES_HISTORY:
                topics.append(common_enums.InitializationEventExchangeTopics.TRADES.value)
            for topic in topics:
                self.logger.debug(f"Trading mode [{self.exchange_manager.exchange_name}] start complete. "
                                  f"Now waiting for {topic} full initialisation.")
                await util.wait_for_topic_init(self.exchange_manager, timeout, topic)
            self.logger.debug(
                f"Trading mode requirements init complete: {', '.join(t for t in topics)} initialisation completed."
            )
            return True
        except (asyncio.TimeoutError, concurrent.futures.TimeoutError):
            self.logger.error(f"Initialization took more than {timeout} seconds")
        return False

    async def init_user_inputs(self, should_clear_inputs):
        if should_clear_inputs:
            await commons_configuration.clear_user_inputs(
                databases.RunDatabasesProvider.instance().get_run_db(self.trading_mode.bot_id)
            )
        await self._register_and_apply_required_user_inputs(
            script_keywords.get_base_context(self.trading_mode, init_call=True)
        )

    async def _register_and_apply_required_user_inputs(self, context):
        if self.trading_mode.ALLOW_CUSTOM_TRIGGER_SOURCE:
            # register activating topics user input
            activation_topic_values = [
                common_enums.ActivationTopics.EVALUATION_CYCLE.value,
                common_enums.ActivationTopics.FULL_CANDLES.value,
                common_enums.ActivationTopics.IN_CONSTRUCTION_CANDLES.value
            ]
            await script_keywords.get_activation_topics(
                context,
                common_enums.ActivationTopics.EVALUATION_CYCLE.value,
                activation_topic_values
            )
        try:
            await self._apply_exchange_side_config(context)
        except Exception as err:
            # TODO important error to display
            self.logger.exception(err, True, f"Error when applying exchange side config: {err}")

    async def _apply_exchange_side_config(self, context):
        # can be slow, call in a task if necessary
        if context.exchange_manager.is_future:
            if not self._is_ready_to_trade.is_set():
                await util.wait_for_topic_init(self.exchange_manager, self.CONFIG_INIT_TIMEOUT,
                                               common_enums.InitializationEventExchangeTopics.CONTRACTS.value)
            await script_keywords.set_leverage(context, await script_keywords.user_select_leverage(context))

    async def _wait_for_symbol_prices_and_profitability_init(self, timeout) -> bool:
        try:
            await util.wait_for_topic_init(self.exchange_manager, timeout,
                                           common_enums.InitializationEventExchangeTopics.PRICE.value)
            await util.wait_for_topic_init(self.exchange_manager, timeout,
                                           common_enums.InitializationEventExchangeTopics.PROFITABILITY.value)
        except (asyncio.TimeoutError, concurrent.futures.TimeoutError):
            self.logger.error(f"Symbol price initialization took more than {timeout} seconds")
        return False

    @classmethod
    def producer_exchange_wide_lock(cls, exchange_manager) -> asyncio_tools.RLock():
        try:
            return cls.PRODUCER_LOCKS_BY_EXCHANGE_ID[exchange_manager.id]
        except KeyError:
            lock = asyncio_tools.RLock()
            cls.PRODUCER_LOCKS_BY_EXCHANGE_ID[exchange_manager.id] = lock
            return lock

    @classmethod
    def delete_producer_exchange_wide_lock(cls, exchange_manager):
        if exchange_manager.id in cls.PRODUCER_LOCKS_BY_EXCHANGE_ID:
            cls.PRODUCER_LOCKS_BY_EXCHANGE_ID.pop(
                exchange_manager.id, None
            )
