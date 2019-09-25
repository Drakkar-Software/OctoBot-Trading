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

import os
from abc import ABCMeta

from octobot_commons.config import load_config
from octobot_commons.constants import TENTACLES_TRADING_PATH, TENTACLE_DEFAULT_CONFIG
from octobot_commons.logging.logging_util import get_logger
from octobot_commons.tentacles_management.abstract_tentacle import AbstractTentacle
from octobot_trading.constants import TENTACLES_TRADING_MODE_PATH, TRADING_MODE_REQUIRED_STRATEGIES_MIN_COUNT, \
    TRADING_MODE_REQUIRED_STRATEGIES


class AbstractTradingMode(AbstractTentacle):
    __metaclass__ = ABCMeta

    def __init__(self, config, exchange_manager):
        super().__init__()
        self.config: dict = config
        self.exchange_manager = exchange_manager
        self.trading_config = None

        self.logger = get_logger(self.get_name())

        self.strategy_instances_by_classes: dict = {}

    def get_name(self) -> str:
        return self.__class__.__name__

    @classmethod
    def get_tentacle_folder(cls) -> str:
        return TENTACLES_TRADING_PATH

    @classmethod
    def get_config_tentacle_type(cls) -> str:
        return TENTACLES_TRADING_MODE_PATH

    @staticmethod
    def is_backtestable() -> bool:
        return True

    async def initialize(self) -> None:
        await self.create_producers()
        await self.create_consumers()

    async def create_producers(self) -> None:
        raise NotImplementedError("create_producers not implemented")

    async def create_consumers(self) -> None:
        raise NotImplementedError("create_consumers not implemented")

    def load_config(self) -> None:
        config_file = self.get_config_file_name()
        # try with this class name
        if os.path.isfile(config_file):
            self.trading_config = load_config(config_file)

        # set default config if nothing found
        if not self.trading_config:
            self.set_default_config()

    # to implement in subclasses if config is necessary
    def set_default_config(self) -> None:
        pass

    @classmethod
    def get_parent_trading_mode_classes(cls, higher_parent_class_limit=None):
        return [
            class_type
            for class_type in cls.mro()
            if (higher_parent_class_limit if higher_parent_class_limit else AbstractTradingMode) in class_type.mro()
        ]

    """
    Strategy related methods
    """

    @classmethod
    def get_required_strategies_names_and_count(cls, trading_mode_config=None):
        config = trading_mode_config or cls.get_specific_config()
        if TRADING_MODE_REQUIRED_STRATEGIES in config:
            return config[TRADING_MODE_REQUIRED_STRATEGIES], cls.get_required_strategies_count(config)
        raise Exception(f"'{TRADING_MODE_REQUIRED_STRATEGIES}' is missing in {cls.get_config_file_name()}")

    @classmethod
    def get_default_strategies(cls):
        config = cls.get_specific_config()
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

    """
    TODO
    """
    # def __init_strategies_instances(self, symbol, all_strategy_instances):
    #     all_strategy_classes = [s.__class__ for s in all_strategy_instances]
    #     required_strategies, required_strategies_min_count = self.get_required_strategies()
    #     missing_strategies = []
    #     found_strategy_count = 0
    #     for required_class in required_strategies:
    #         if required_class in all_strategy_classes:
    #             self.strategy_instances_by_classes[symbol][required_class] = \
    #                 all_strategy_instances[all_strategy_classes.index(required_class)]
    #             found_strategy_count += 1
    #         else:
    #             subclass = get_class(self.config, required_class)
    #             if subclass in all_strategy_classes:
    #                 self.strategy_instances_by_classes[symbol][required_class] = \
    #                     all_strategy_instances[all_strategy_classes.index(subclass)]
    #                 found_strategy_count += 1
    #         if required_class not in self.strategy_instances_by_classes[symbol]:
    #             missing_strategies.append(required_class)
    #     if found_strategy_count < required_strategies_min_count:
    #         for missing_strategy in missing_strategies:
    #             self.logger.error(f"No instance of {missing_strategy.__name__} or advanced equivalent found, "
    #                               f"{self.get_name()} trading mode can't work properly ! Maybe this strategy is "
    #                               f"disabled in tentacles/Evaluator/evaluator_config.json (missing "
    #                               f"{required_strategies_min_count-found_strategy_count} out of "
    #                               f"{required_strategies_min_count} minimum required strategies).")
    #
    # @classmethod
    # def get_required_strategies(cls, trading_mode_config=None):
    #     config = trading_mode_config or cls.get_specific_config()
    #     if TRADING_MODE_REQUIRED_STRATEGIES in config:
    #         strategies_classes = []
    #         for class_string in config[TRADING_MODE_REQUIRED_STRATEGIES]:
    #             s_class = get_deep_class_from_string(class_string, Strategies)
    #             if s_class is not None:
    #                 if s_class not in strategies_classes:
    #                     strategies_classes.append(s_class)
    #             else:
    #                 raise TentacleNotFound(f'{class_string} is not found, Octobot can\'t use {cls.get_name()},'
    #                                        f' please check {cls.get_name()}{cls.get_config_file_name()}')
    #
    #         return strategies_classes, cls.get_required_strategies_count(config)
    #     else:
    #         raise Exception(f"'{TRADING_MODE_REQUIRED_STRATEGIES}' is missing in {cls.get_config_file_name()}")
