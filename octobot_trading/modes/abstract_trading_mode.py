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
import abc
import contextlib
import decimal

import octobot_commons.constants as common_constants
import octobot_commons.enums as common_enums
import octobot_commons.logging as logging
import octobot_commons.tentacles_management as abstract_tentacle

import async_channel.constants as channel_constants
import async_channel.channels as channels

import octobot_tentacles_manager.api as tentacles_manager_api
import octobot_tentacles_manager.configuration as tm_configuration

import octobot_trading.constants as constants
import octobot_trading.enums as enums
import octobot_trading.exchange_channel as exchanges_channel
import octobot_trading.modes.modes_factory as modes_factory
import octobot_trading.modes.channel.abstract_mode_producer as abstract_mode_producer
import octobot_trading.modes.channel.abstract_mode_consumer as abstract_mode_consumer
import octobot_trading.modes.mode_config as mode_config
import octobot_trading.modes.modes_util as modes_util
import octobot_trading.exchanges.util.exchange_util as exchange_util
import octobot_trading.signals as signals


class AbstractTradingMode(abstract_tentacle.AbstractTentacle):
    __metaclass__ = abc.ABCMeta
    USER_INPUT_TENTACLE_TYPE = common_enums.UserInputTentacleTypes.TRADING_MODE
    ALLOW_CUSTOM_TRIGGER_SOURCE = False
    HISTORIZE_USER_INPUT_CONFIG = True

    MODE_PRODUCER_CLASSES = []
    MODE_CONSUMER_CLASSES = []
    # maximum seconds before sending a trading signal if orders are slow to create on exchange
    TRADING_SIGNAL_TIMEOUT = 10
    REQUIRE_TRADES_HISTORY = False   # set True when this trading mode needs the trade history to operate
    ALLOW_CANCEL_BEFORE_BUY_SIGNALS = True  # set False if trade signals from this trading mode should NOT be
    # reordered to process cancel signals first
    SUPPORTS_INITIAL_PORTFOLIO_OPTIMIZATION = False  # set True when self._optimize_initial_portfolio is implemented
    SUPPORTS_HEALTH_CHECK = False   # set True when self.health_check is implemented
    ENABLE_HEALTH_CHECK = "enable_health_check"
    HEALTH_CHECK_INTERVAL = common_constants.DAYS_TO_SECONDS

    def __init__(self, config, exchange_manager):
        super().__init__()
        self.logger = logging.get_logger(self.get_name())

        # Global OctoBot configuration
        self.config: dict = config

        # Mode related exchange manager instance
        self.exchange_manager = exchange_manager

        # The id of the OctoBot using this trading mode
        self.bot_id: str = None

        # Trading Mode specific config (Is loaded from tentacle specific file)
        self.trading_config: dict = None

        # Trading Mode specific config snapshot before a config update
        self.previous_trading_config: dict = None

        # If this mode is enabled
        self.enabled: bool = True

        # Specified Cryptocurrency for this instance (Should be None if wildcard)
        self.cryptocurrency: str = None

        # Symbol is the cryptocurrency pair (Should be None if wildcard)
        self.symbol: str = None

        # Time_frame is the chart time frame (Should be None if wildcard)
        self.time_frame = None

        # producers is the list of producers created by this trading mode
        self.producers = []

        # producers is the list of consumers created by this trading mode
        self.consumers = []

        # True when this trading mode is waken up only after full candles close
        self.is_triggered_after_candle_close = False

        # True when initialization orders are waiting to be created
        self.are_initialization_orders_pending = False

        # When True, health check will be performed when calling trading_mode_trigger
        self.is_health_check_enabled = False
        self._last_health_check_time = 0

    # Used to know the current state of the trading mode.
    # Overwrite in subclasses
    def get_current_state(self) -> tuple:
        """
        :return: (str, float): (current state description, current state value)
        """
        return "N/A", 0

    @classmethod
    def get_is_cryptocurrency_wildcard(cls) -> bool:
        """
        :return: True if the mode is not cryptocurrency dependant else False
        """
        return True

    @classmethod
    def get_is_symbol_wildcard(cls) -> bool:
        """
        :return: True if the mode is not symbol dependant else False
        """
        return True

    @classmethod
    def get_is_time_frame_wildcard(cls) -> bool:
        """
        :return: True if the mode is not time_frame dependant else False
        """
        return True

    @classmethod
    def get_supported_exchange_types(cls) -> list:
        """
        :return: The list of supported exchange types
        """
        return [
            enums.ExchangeTypes.SPOT
        ]

    def get_mode_producer_classes(self) -> list:
        return self.MODE_PRODUCER_CLASSES

    def get_mode_consumer_classes(self) -> list:
        return self.MODE_CONSUMER_CLASSES

    def should_emit_trading_signal(self) -> bool:
        """
        :return: True if the mode should be emitting trading signals according to configuration and trading environment
        """
        return not self.exchange_manager.is_backtesting and mode_config.is_trading_signal_emitter(self)

    def get_trading_signal_identifier(self) -> str:
        """
        :return: The identifier of the trading signal from config or the name of the tentacle if missing
        """
        try:
            return self.trading_config[common_constants.CONFIG_TRADING_SIGNALS_STRATEGY] or self.get_name()
        except KeyError:
            return self.get_name()

    def is_following_trading_signals(self) -> bool:
        """
        :return: True when the trading mode is following trading signals
        """
        return False

    @classmethod
    def get_is_trading_on_exchange(cls, exchange_name,
                                   tentacles_setup_config: tm_configuration.TentaclesSetupConfiguration) -> bool:
        """
        :return: When returning false, the associated exchange_manager.is_trading will be set to false, which will
        prevent the initialization of trade related elements. Default is True
        """
        return True

    @classmethod
    def is_ignoring_cancelled_orders_trades(cls) -> bool:
        """
        :return: True if trades created by cancelled orders should be ignored and not stored in trades manager
        """
        return False

    @classmethod
    def get_parent_trading_mode_classes(cls, higher_parent_class_limit=None) -> list:
        return [
            class_type
            for class_type in cls.mro()
            if (higher_parent_class_limit if higher_parent_class_limit else AbstractTradingMode) in class_type.mro()
        ]

    @staticmethod
    def is_backtestable() -> bool:
        """
        Should be overwritten
        :return: True if the TradingMode can be used in a backtesting else False
        """
        return True

    async def initialize(self, trading_config=None, auto_start=True) -> None:
        """
        Triggers producers and consumers creation
        """
        await self.reload_config(self.exchange_manager.bot_id, trading_config=trading_config)
        self.producers = await self.create_producers(auto_start)
        self.consumers = await self.create_consumers()

    async def stop(self) -> None:
        """
        Stops all producers and consumers
        """
        for producer in self.producers:
            await producer.stop()
        for consumer in self.consumers:
            await consumer.stop()
        self.exchange_manager = None

    async def create_producers(self, auto_start) -> list:
        """
        Creates the instance of producers listed in MODE_PRODUCER_CLASSES
        :return: the list of producers created
        """
        return [
            await self._create_mode_producer(mode_producer_class, auto_start)
            for mode_producer_class in self.get_mode_producer_classes()
        ]

    async def _create_mode_producer(self, mode_producer_class, auto_start):
        """
        Creates a new :mode_producer_class: instance and starts it
        :param mode_producer_class: the trading mode producer class to create
        :return: the producer class created
        """
        mode_producer = mode_producer_class(
            exchanges_channel.get_chan(constants.MODE_CHANNEL, self.exchange_manager.id),
            self.config, self, self.exchange_manager)
        if auto_start:
            await mode_producer.run()
        return mode_producer

    async def start_producers(self):
        """
        Should be used if producers got created with auto_start=False
        """
        for producer in self.producers:
            await producer.run()

    async def create_consumers(self) -> list:
        """
        Creates the instance of consumers listed in MODE_CONSUMER_CLASSES
        :return: the list of consumers created
        """
        base_consumers = [
            await self._create_mode_consumer(mode_consumer_class)
            for mode_consumer_class in self.get_mode_consumer_classes()
        ]
        if user_input_consumer := await self._create_user_input_consumer():
            base_consumers.append(user_input_consumer)

        return base_consumers

    async def _create_user_input_consumer(self):
        try:
            import octobot_services.channel as services_channels
            user_commands_consumer = \
                await channels.get_chan(services_channels.UserCommandsChannel.get_name()).new_consumer(
                    self.user_commands_callback,
                    {"bot_id": self.bot_id, "subject": self.get_name()}
                )
            return user_commands_consumer
        except KeyError:
            self.logger.debug(f"{services_channels.UserCommandsChannel.get_name()} unavailable")
        except ImportError:
            self.logger.warning("Can't connect to services channels")
        return None

    async def user_commands_callback(self, bot_id, subject, action, data) -> None:
        self.logger.debug(f"Received {action} command")
        if action == common_enums.UserCommands.MANUAL_TRIGGER.value:
            self.logger.debug(f"Triggering trading mode from {action} command with data: {data}")
            await self._manual_trigger(data)
        if action == common_enums.UserCommands.RELOAD_CONFIG.value:
            await self.reload_config(bot_id)
            self.logger.debug("Reloaded configuration")
        elif action == common_enums.UserCommands.CLEAR_PLOTTING_CACHE.value:
            await modes_util.clear_plotting_cache(self)
        elif action == common_enums.UserCommands.CLEAR_SIMULATED_ORDERS_CACHE.value:
            await modes_util.clear_simulated_orders_cache(self)
        elif action == common_enums.UserCommands.OPTIMIZE_INITIAL_PORTFOLIO.value:
            if self.SUPPORTS_INITIAL_PORTFOLIO_OPTIMIZATION:
                await self.optimize_initial_portfolio([], {})
        elif action == common_enums.UserCommands.TRIGGER_HEALTH_CHECK.value:
            if self.SUPPORTS_HEALTH_CHECK:
                await self.health_check([], {})

    async def _manual_trigger(self, data):
        kwargs = {
            "trigger_source": common_enums.TriggerSource.MANUAL.value
        }
        kwargs.update(data.get("kwargs", {}))
        for producer in self.producers:
            await producer.trigger(**kwargs)

    def enabled_health_check_in_config(self) -> bool:
        try:
            return self.trading_config.get(self.ENABLE_HEALTH_CHECK, False)
        except AttributeError:
            # when self.trading_config is None, should not happen
            return False

    @classmethod
    def get_forced_updater_channels(cls) -> set[str]:
        return set()

    def _health_check_interval_expired(self) -> bool:
        return self.exchange_manager.exchange.get_exchange_current_time() - self._last_health_check_time \
            > self.HEALTH_CHECK_INTERVAL

    def is_health_check_required(self) -> bool:
        return self.SUPPORTS_HEALTH_CHECK and self.is_health_check_enabled and self._health_check_interval_expired()

    async def health_check(self, chained_orders: list, tickers: dict) -> list:
        self._last_health_check_time = self.exchange_manager.exchange.get_exchange_current_time()
        if not self.producers:
            # nothing to do
            return []
        async with self._single_exchange_operation("health check") as continue_operation:
            if not continue_operation:
                return []
            return await self.single_exchange_process_health_check(chained_orders, tickers)

    async def single_exchange_process_health_check(self, chained_orders: list, tickers: dict) -> list:
        raise NotImplementedError("single_exchange_process_health_check is not implemented")

    async def optimize_initial_portfolio(self, sellable_assets: list, tickers: dict) -> list:
        if not self.producers:
            # nothing to do
            return []
        # first acquire trading mode lock to be sure we are not in during trading mode iteration
        async with self.producers[0].trading_mode_trigger():
            async with self._single_exchange_operation("portfolio optimization") as continue_operation:
                if not continue_operation:
                    return []
                target_asset = exchange_util.get_common_traded_quote(self.exchange_manager)
                if target_asset is None:
                    self.logger.error(f"Impossible to optimize initial portfolio with different quotes in traded pairs")
                    return []
                self.logger.info(f"Starting portfolio optimization using trading mode with symbol {self.symbol}")
                created_orders = await self.single_exchange_process_optimize_initial_portfolio(
                    sellable_assets, target_asset, tickers
                )
                if not created_orders:
                    self.logger.info("Optimizing portfolio: no order to create")
                await modes_util.notify_portfolio_optimization_complete()
                return created_orders

    async def single_exchange_process_optimize_initial_portfolio(
        self, sellable_assets: list, target_asset: str, tickers: dict
    ) -> list:
        raise NotImplementedError("single_exchange_process_optimize_initial_portfolio is not implemented")

    @contextlib.asynccontextmanager
    async def _single_exchange_operation(self, operation_name):
        is_the_single_operation = not self.producers[0].producer_exchange_wide_lock(self.exchange_manager).locked()
        if is_the_single_operation:
            # already locked by another trading mode instance: this other trading mode will do the operation
            self.logger.debug(
                f"[Single exchange operation]: triggering '{operation_name}' for trading mode with symbol "
                f"{self.symbol} [{self.exchange_manager.exchange_name}]."
            )
        else:
            # already locked by another trading mode instance: this other trading mode will do the operation
            self.logger.debug(
                f"[Single exchange operation]: skipping '{operation_name}' for trading mode with symbol {self.symbol} "
                f"[{self.exchange_manager.exchange_name}]: "
                f"{operation_name} already in progress. Waiting for initial {operation_name} to complete."
            )
        async with self.producers[0].producer_exchange_wide_lock(self.exchange_manager):
            yield is_the_single_operation

    @classmethod
    def get_user_commands(cls) -> dict:
        """
        Return the dict of user commands for this tentacle
        :return: the commands dict
        """
        commands = {}
        if cls.SUPPORTS_INITIAL_PORTFOLIO_OPTIMIZATION:
            commands[common_enums.UserCommands.OPTIMIZE_INITIAL_PORTFOLIO.value] = {}
        if cls.SUPPORTS_HEALTH_CHECK:
            commands[common_enums.UserCommands.TRIGGER_HEALTH_CHECK.value] = {}
        return commands

    async def _create_mode_consumer(self, mode_consumer_class):
        """
        Creates a new :mode_consumer_class: instance and subscribe this new consumer to the trading mode channel
        :param mode_consumer_class: the trading mode consumer class to create
        :return: the consumer class created
        """
        mode_consumer = mode_consumer_class(self)
        await exchanges_channel.get_chan(constants.MODE_CHANNEL, self.exchange_manager.id).new_consumer(
            consumer_instance=mode_consumer,
            trading_mode_name=self.get_name(),
            cryptocurrency=self.cryptocurrency if self.cryptocurrency else channel_constants.CHANNEL_WILDCARD,
            symbol=self.symbol if self.symbol else channel_constants.CHANNEL_WILDCARD,
            time_frame=self.time_frame if self.time_frame else channel_constants.CHANNEL_WILDCARD)
        return mode_consumer

    async def reload_config(self, bot_id: str, trading_config=None) -> None:
        """
        Try to load TradingMode tentacle config.
        Calls set_default_config() if the tentacle config is empty
        """
        self.trading_config = trading_config or \
            tentacles_manager_api.get_tentacle_config(self.exchange_manager.tentacles_setup_config, self.__class__)
        # set default config if nothing found
        if not self.trading_config:
            self.set_default_config()
        await self.load_and_save_user_inputs(bot_id)
        for element in self.consumers + self.producers:
            if isinstance(element, (abstract_mode_consumer.AbstractTradingModeConsumer,
                                    abstract_mode_producer.AbstractTradingModeProducer)):
                element.on_reload_config()
                await element.init_user_inputs(False)
        self.logger.debug(f"Using config: {self.trading_config}")

    def get_local_config(self):
        return self.trading_config

    @classmethod
    def create_local_instance(cls, config, tentacles_setup_config, tentacle_config):
        return modes_factory.create_temporary_trading_mode_with_local_config(
            cls, config, tentacle_config
        )

    # to implement in subclasses if config is necessary
    def set_default_config(self) -> None:
        pass

    """
    Strategy related methods
    """

    @classmethod
    def get_required_strategies_names_and_count(
        cls, tentacles_config: tm_configuration.TentaclesSetupConfiguration, trading_mode_config=None
    ):
        config = trading_mode_config or tentacles_manager_api.get_tentacle_config(tentacles_config, cls)
        if constants.TRADING_MODE_REQUIRED_STRATEGIES in config:
            return config[constants.TRADING_MODE_REQUIRED_STRATEGIES], cls.get_required_strategies_count(config)
        raise Exception(f"'{constants.TRADING_MODE_REQUIRED_STRATEGIES}' is missing in configuration file")

    @classmethod
    def get_default_strategies(cls,
                               tentacles_config: tm_configuration.TentaclesSetupConfiguration,
                               trading_mode_config=None):
        config = trading_mode_config or tentacles_manager_api.get_tentacle_config(tentacles_config, cls)
        if common_constants.TENTACLE_DEFAULT_CONFIG in config:
            return config[common_constants.TENTACLE_DEFAULT_CONFIG]

        strategies_classes, _ = cls.get_required_strategies_names_and_count(tentacles_config, config)
        return strategies_classes

    @classmethod
    def get_required_strategies_count(cls, config):
        min_strategies_count = 1
        if constants.TRADING_MODE_REQUIRED_STRATEGIES_MIN_COUNT in config:
            min_strategies_count = config[constants.TRADING_MODE_REQUIRED_STRATEGIES_MIN_COUNT]
        return min_strategies_count

    @classmethod
    def get_required_candles_count(cls, tentacles_setup_config: tm_configuration.TentaclesSetupConfiguration):
        return tentacles_manager_api.get_tentacle_config(tentacles_setup_config, cls).get(
            constants.CONFIG_CANDLES_HISTORY_SIZE_KEY,
            common_constants.DEFAULT_IGNORED_VALUE
        )

    @contextlib.asynccontextmanager
    async def remote_signal_publisher(self, symbol: str):
        async with signals.remote_signal_publisher(self.exchange_manager, symbol, self.should_emit_trading_signal()) \
             as signal_builder:
            yield signal_builder

    async def create_order(self, order, loaded: bool = False, params: dict = None,
                           wait_for_creation=True,
                           creation_timeout=constants.INDIVIDUAL_ORDER_SYNC_TIMEOUT):
        return await signals.create_order(
            self.exchange_manager, self.should_emit_trading_signal(), order,
            loaded=loaded, params=params,
            wait_for_creation=wait_for_creation, creation_timeout=creation_timeout
        )

    async def cancel_order(self, order, ignored_order: object = None) -> bool:
        return await signals.cancel_order(
            self.exchange_manager, self.should_emit_trading_signal(), order,
            ignored_order=ignored_order
        )

    async def cancel_all_orders(
        self,
        symbol: str,
        allow_single_order_cancel_fallback: bool,
        wait_for_cancelling: bool = True,
        cancelling_timeout: float = constants.INDIVIDUAL_ORDER_SYNC_TIMEOUT
    ) -> bool:
        # todo send signals when implementation will be necessary
        return await self.exchange_manager.trader.cancel_all_orders(
            symbol,
            allow_single_order_cancel_fallback,
            wait_for_cancelling=wait_for_cancelling,
            cancelling_timeout=cancelling_timeout
        )

    async def edit_order(self, order,
                         edited_quantity: decimal.Decimal = None,
                         edited_price: decimal.Decimal = None,
                         edited_stop_price: decimal.Decimal = None,
                         edited_current_price: decimal.Decimal = None,
                         params: dict = None) -> bool:
        return await signals.edit_order(
            self.exchange_manager, self.should_emit_trading_signal(), order,
            edited_quantity=edited_quantity,
            edited_price=edited_price,
            edited_stop_price=edited_stop_price,
            edited_current_price=edited_current_price,
            params=params
        )

    async def get_additional_metadata(self, is_backtesting):
        """
        Override if necessary
        """
        return {}

    def flush_trading_mode_consumers(self):
        for consumer in self.get_trading_mode_consumers():
            consumer.flush()

    def get_trading_mode_consumers(self):
        return [
            consumer
            for consumer in self.consumers
            if isinstance(consumer, abstract_mode_consumer.AbstractTradingModeConsumer)
        ]
