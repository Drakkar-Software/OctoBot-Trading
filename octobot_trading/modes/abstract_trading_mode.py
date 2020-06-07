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
from abc import ABCMeta

from octobot_commons.constants import TENTACLE_DEFAULT_CONFIG
from octobot_commons.logging.logging_util import get_logger
from octobot_commons.tentacles_management.abstract_tentacle import AbstractTentacle
from octobot_tentacles_manager.api.configurator import get_tentacle_config
from octobot_trading.constants import TRADING_MODE_REQUIRED_STRATEGIES_MIN_COUNT, TRADING_MODE_REQUIRED_STRATEGIES


class AbstractTradingMode(AbstractTentacle):
    __metaclass__ = ABCMeta

    def __init__(self, config, exchange_manager):
        super().__init__()
        self.logger = get_logger(self.get_name())

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
    def get_is_trading_on_exchange(cls, exchange_name) -> bool:
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
        self.producers = await self.create_producers()
        self.consumers = await self.create_consumers()

    async def stop(self) -> None:
        for producer in self.producers:
            await producer.stop()
        for consumer in self.consumers:
            await consumer.stop()
        self.exchange_manager = None

    async def create_producers(self) -> list:
        raise NotImplementedError("create_producers not implemented")

    async def create_consumers(self) -> list:
        raise NotImplementedError("create_consumers not implemented")

    def load_config(self) -> None:
        # try with this class name
        self.trading_config = get_tentacle_config(self.__class__)

        # set default config if nothing found
        if not self.trading_config:
            self.set_default_config()

    # to implement in subclasses if config is necessary
    def set_default_config(self) -> None:
        pass

    """
    Strategy related methods
    """

    @classmethod
    def get_required_strategies_names_and_count(cls, trading_mode_config=None):
        config = trading_mode_config or get_tentacle_config(cls)
        if TRADING_MODE_REQUIRED_STRATEGIES in config:
            return config[TRADING_MODE_REQUIRED_STRATEGIES], cls.get_required_strategies_count(config)
        raise Exception(f"'{TRADING_MODE_REQUIRED_STRATEGIES}' is missing in configuration file")

    @classmethod
    def get_default_strategies(cls, trading_mode_config=None):
        config = trading_mode_config or get_tentacle_config(cls)
        if TENTACLE_DEFAULT_CONFIG in config:
            return config[TENTACLE_DEFAULT_CONFIG]

        strategies_classes, _ = cls.get_required_strategies_names_and_count(config)
        return strategies_classes

    @classmethod
    def get_required_strategies_count(cls, config):
        min_strategies_count = 1
        if TRADING_MODE_REQUIRED_STRATEGIES_MIN_COUNT in config:
            min_strategies_count = config[TRADING_MODE_REQUIRED_STRATEGIES_MIN_COUNT]
        return min_strategies_count
