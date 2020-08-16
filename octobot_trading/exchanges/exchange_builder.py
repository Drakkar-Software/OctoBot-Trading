# cython: language_level=3
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
#  Lesser General License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
from octobot_commons.logging.logging_util import get_logger

from octobot_trading.api.modes import create_trading_modes
from octobot_trading.constants import CONFIG_EXCHANGES, CONFIG_EXCHANGE_SANDBOXED
from octobot_trading.errors import TradingModeIncompatibility
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.exchanges.exchanges import Exchanges
from octobot_trading.traders.trader import Trader
from octobot_trading.traders.trader_simulator import TraderSimulator
from octobot_trading.util import is_trader_simulator_enabled, is_trader_enabled
from octobot_trading.util.trading_config_util import get_activated_trading_mode


class ExchangeBuilder:
    def __init__(self, config, exchange_name):
        self.logger = get_logger(self.__class__.__name__)
        self.config: dict = config
        self.exchange_name: str = exchange_name

        self.exchange_manager: ExchangeManager = ExchangeManager(self.config, self.exchange_name)

        self._is_using_trading_modes: bool = True
        self._matrix_id: str = None
        self._bot_id: str = None

        self._tentacles_setup_config = None

    async def build(self):
        """
        Build the exchange
        """
        try:
            await self._build_exchange_manager()
        except Exception as e:
            # stop exchange manager if an exception occurred when building it
            await self.exchange_manager.stop(warning_on_missing_elements=False)
            raise e
        return self.exchange_manager

    async def _build_exchange_manager(self):
        if self._is_using_trading_modes:
            trading_mode_class = get_activated_trading_mode(self._tentacles_setup_config)
            # handle exchange related requirements if the activated trading mode has any
            self._register_trading_modes_requirements(trading_mode_class)

        self.exchange_manager.tentacles_setup_config = self._tentacles_setup_config
        await self.exchange_manager.initialize()

        # initialize exchange for trading if not collecting
        if not self.exchange_manager.is_collecting:

            # initialize trader
            if self.exchange_manager.trader is not None:
                await self._build_trader()

            # create trading modes
            if self._is_using_trading_modes:
                if self.exchange_manager.is_trading:
                    self.exchange_manager.trading_modes = await self._build_trading_modes(trading_mode_class)
                else:
                    self.logger.info(f"{self.exchange_name} exchange is online and won't be trading")

        # add to global exchanges
        Exchanges.instance().add_exchange(self.exchange_manager, self._matrix_id)

    async def _build_trader(self):
        try:
            # check traders activation
            if not is_trader_enabled(self.config) and not is_trader_simulator_enabled(self.config):
                raise ValueError(f"No trader simulator nor real trader activated on "
                                 f"{self.exchange_manager.exchange_name}")

            await self.exchange_manager.trader.initialize()
        except ValueError as e:
            self.logger.error(f"An error occurred when creating trader : {e}")
            raise e

    def _register_trading_modes_requirements(self, trading_mode_class):
        self.exchange_manager.is_trading = trading_mode_class.get_is_trading_on_exchange(self.exchange_name)

    async def _build_trading_modes(self, trading_mode_class):
        try:
            return await create_trading_modes(self.config,
                                              self.exchange_manager,
                                              trading_mode_class,
                                              self._bot_id)
        except TradingModeIncompatibility as e:
            raise e
        except Exception as e:
            self.logger.error(f"An error occurred when initializing trading mode : {e}")
            raise e

    """
    Builder methods
    """
    def is_backtesting(self, backtesting_instance):
        self.exchange_manager.is_backtesting = True
        self.exchange_manager.backtesting = backtesting_instance
        return self

    def is_sandboxed(self, sandboxed: bool):
        self.exchange_manager.is_sandboxed = sandboxed
        return self

    def is_simulated(self):
        self.exchange_manager.is_simulated = True
        self.exchange_manager.trader = TraderSimulator(self.config, self.exchange_manager)
        return self

    def is_real(self):
        self.exchange_manager.is_simulated = False
        self.exchange_manager.trader = Trader(self.config, self.exchange_manager)
        return self

    def is_margin(self, use_margin=True):
        self.exchange_manager.is_margin = use_margin
        return self

    def is_future(self, use_future=True):
        self.exchange_manager.is_future = use_future
        return self

    def is_spot_only(self, use_spot_only=True):
        self.exchange_manager.is_spot_only = use_spot_only
        return self

    def is_rest_only(self):
        self.exchange_manager.rest_only = True
        return self

    def is_exchange_only(self):
        self.exchange_manager.exchange_only = True
        return self

    def is_collecting(self):
        self.exchange_manager.is_collecting = True
        return self

    def is_ignoring_config(self):
        self.exchange_manager.ignore_config = True
        return self

    def use_tentacles_setup_config(self, tentacles_setup_config):
        self._tentacles_setup_config = tentacles_setup_config
        return self

    def set_bot_id(self, bot_id):
        self._bot_id = bot_id
        return self

    def disable_trading_mode(self):
        self._is_using_trading_modes = False
        return self

    def has_matrix(self, matrix_id):
        self._matrix_id = matrix_id
        return self
