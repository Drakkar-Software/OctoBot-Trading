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
import octobot_commons.configuration as commons_configuration
import octobot_commons.tentacles_management as abstract_tentacle
import octobot_commons.authentication as authentication

import async_channel.constants as channel_constants
import async_channel.channels as channels

import octobot_tentacles_manager.api as tentacles_manager_api
import octobot_tentacles_manager.configuration as tm_configuration

import octobot_trading.constants as constants
import octobot_trading.enums as enums
import octobot_trading.exchange_channel as exchanges_channel
import octobot_trading.modes.script_keywords as script_keywords
import octobot_trading.modes.modes_factory as modes_factory
import octobot_trading.modes.channel.abstract_mode_producer as abstract_mode_producer
import octobot_trading.modes.channel.abstract_mode_consumer as abstract_mode_consumer
import octobot_trading.personal_data.orders as orders
import octobot_trading.signals as signals


class AbstractTradingMode(abstract_tentacle.AbstractTentacle):
    __metaclass__ = abc.ABCMeta
    USER_INPUT_TENTACLE_TYPE = common_enums.UserInputTentacleTypes.TRADING_MODE

    MODE_PRODUCER_CLASSES = []
    MODE_CONSUMER_CLASSES = []
    # maximum seconds before sending a trading signal if orders are slow to create on exchange
    TRADING_SIGNAL_TIMEOUT = 10

    def __init__(self, config, exchange_manager):
        super().__init__()
        self.logger = logging.get_logger(self.get_name())

        # Global OctoBot configuration
        self.config: dict = config

        # Mode related exchange manager instance
        self.exchange_manager = exchange_manager

        # The id of the OctoBot using this trading mode
        self.bot_id: str = None

        # Evaluator specific config (Is loaded from tentacle specific file)
        self.trading_config: dict = None

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

    def should_emit_trading_signals_user_input(self, inputs: dict):
        if self.UI.user_input(
            common_constants.CONFIG_EMIT_TRADING_SIGNALS, common_enums.UserInputTypes.BOOLEAN, False, inputs,
            title="Emit trading signals on Astrolab for people to follow.",
            order=commons_configuration.UserInput.MAX_ORDER - 2
        ):
            self.UI.user_input(
                common_constants.CONFIG_TRADING_SIGNALS_STRATEGY, common_enums.UserInputTypes.TEXT, self.get_name(),
                inputs,
                title="Name of the strategy to send signals on.",
                order=commons_configuration.UserInput.MAX_ORDER - 1,
                other_schema_values={"minLength": 0}
            )

    def is_trading_signal_emitter(self) -> bool:
        """
        :return: True if the mode should be emitting trading signals according to configuration
        """
        try:
            return self.trading_config[common_constants.CONFIG_EMIT_TRADING_SIGNALS]
        except KeyError:
            return False

    def should_emit_trading_signal(self) -> bool:
        """
        :return: True if the mode should be emitting trading signals according to configuration and trading environment
        """
        return not self.exchange_manager.is_backtesting and self.is_trading_signal_emitter()

    def get_trading_signal_identifier(self) -> str:
        """
        :return: The identifier of the trading signal from config or the name of the tentacle if missing
        """
        try:
            return self.trading_config[common_constants.CONFIG_TRADING_SIGNALS_STRATEGY] or self.get_name()
        except KeyError:
            return self.get_name()

    @classmethod
    def get_is_trading_on_exchange(cls, exchange_name,
                                   tentacles_setup_config: tm_configuration.TentaclesSetupConfiguration) -> bool:
        """
        :return: When returning false, the associated exchange_manager.is_trading will be set to false, which will
        prevent the initialization of trade related elements. Default is True
        """
        return True

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

    async def initialize(self) -> None:
        """
        Triggers producers and consumers creation
        """
        await self.reload_config(self.exchange_manager.bot_id)
        self.producers = await self.create_producers()
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

    async def create_producers(self) -> list:
        """
        Creates the instance of producers listed in MODE_PRODUCER_CLASSES
        :return: the list of producers created
        """
        return [
            await self._create_mode_producer(mode_producer_class)
            for mode_producer_class in self.get_mode_producer_classes()
        ]

    async def _create_mode_producer(self, mode_producer_class):
        """
        Creates a new :mode_producer_class: instance and starts it
        :param mode_producer_class: the trading mode producer class to create
        :return: the producer class created
        """
        mode_producer = mode_producer_class(
            exchanges_channel.get_chan(constants.MODE_CHANNEL, self.exchange_manager.id),
            self.config, self, self.exchange_manager)
        await mode_producer.run()
        return mode_producer

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
        if action == common_enums.UserCommands.RELOAD_CONFIG.value:
            await self.reload_config(bot_id)
            self.logger.debug("Reloaded configuration")


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

    async def reload_config(self, bot_id: str) -> None:
        """
        Try to load TradingMode tentacle config.
        Calls set_default_config() if the tentacle config is empty
        """
        self.trading_config = tentacles_manager_api.get_tentacle_config(self.exchange_manager.tentacles_setup_config,
                                                                        self.__class__)
        # set default config if nothing found
        if not self.trading_config:
            self.set_default_config()
        await self.load_and_save_user_inputs(bot_id)
        for element in self.consumers + self.producers:
            if isinstance(element, (abstract_mode_consumer.AbstractTradingModeConsumer,
                                    abstract_mode_producer.AbstractTradingModeProducer)):
                element.on_reload_config()

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
    def get_required_strategies_names_and_count(cls,
                                                tentacles_config: tm_configuration.TentaclesSetupConfiguration,
                                                trading_mode_config=None):
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
        if self.should_emit_trading_signal():
            try:
                async with signals.SignalPublisher.instance().remote_signal_bundle_builder(
                    symbol,
                    self.get_trading_signal_identifier(),
                    self.TRADING_SIGNAL_TIMEOUT,
                    signals.TradingSignalBundleBuilder,
                    (self.get_name(), )
                ) as signal_builder:
                    yield signal_builder
            except (authentication.AuthenticationRequired, authentication.UnavailableError) as e:
                self.logger.exception(e, True, f"Failed to send trading signals: {e}")
        else:
            yield None

    async def create_order(self, order, loaded: bool = False, params: dict = None, pre_init_callback=None):
        order_pf_percent = f"0{script_keywords.QuantityType.PERCENT.value}"
        if self.should_emit_trading_signal():
            percent = await orders.get_order_size_portfolio_percent(
                self.exchange_manager,
                order.origin_quantity,
                order.side,
                order.symbol
            )
            order_pf_percent = f"{float(percent)}{script_keywords.QuantityType.PERCENT.value}"
        created_order = await self.exchange_manager.trader.create_order(
            order, loaded=loaded, params=params, pre_init_callback=pre_init_callback
        )
        if created_order is not None and self.should_emit_trading_signal():
            signals.SignalPublisher.instance().get_signal_bundle_builder(order.symbol).add_created_order(
                    created_order, self.exchange_manager, target_amount=order_pf_percent
                )
        return created_order

    async def cancel_order(self, order, ignored_order: object = None) -> bool:
        cancelled = await self.exchange_manager.trader.cancel_order(order, ignored_order=ignored_order)
        if self.should_emit_trading_signal() and cancelled:
            signals.SignalPublisher.instance().get_signal_bundle_builder(order.symbol).add_cancelled_order(
                order, self.exchange_manager
            )
        return cancelled

    async def edit_order(self, order,
                         edited_quantity: decimal.Decimal = None,
                         edited_price: decimal.Decimal = None,
                         edited_stop_price: decimal.Decimal = None,
                         edited_current_price: decimal.Decimal = None,
                         params: dict = None) -> bool:
        changed = await self.exchange_manager.trader.edit_order(
            order,
            edited_quantity=edited_quantity,
            edited_price=edited_price,
            edited_stop_price=edited_stop_price,
            edited_current_price=edited_current_price,
            params=params
        )
        if self.should_emit_trading_signal() and changed:
            signals.SignalPublisher.instance().get_signal_bundle_builder(order.symbol).add_edited_order(
                order,
                self.exchange_manager,
                updated_target_amount=edited_quantity,
                updated_limit_price=edited_price,
                updated_stop_price=edited_stop_price,
                updated_current_price=edited_current_price,
            )
        return changed

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

