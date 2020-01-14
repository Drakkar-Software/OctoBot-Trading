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
from octobot_commons.constants import CONFIG_TRADING_FILE_PATH

from octobot_commons.logging.logging_util import get_logger

from octobot_trading.api.modes import create_trading_mode, init_trading_mode_config
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.exchanges.exchanges import Exchanges
from octobot_trading.traders.trader import Trader
from octobot_trading.traders.trader_simulator import TraderSimulator
from octobot_trading.util import is_trader_simulator_enabled, is_trader_enabled


class ExchangeFactory:
    def __init__(self, config, exchange_name,
                 is_simulated=False,
                 is_backtesting=False,
                 rest_only=False,
                 ignore_config=False,
                 is_sandboxed=False,
                 is_collecting=False,
                 exchange_only=False,
                 backtesting_files=None):
        self.logger = get_logger(self.__class__.__name__)
        self.config = config
        self.exchange_name = exchange_name
        self.is_simulated = is_simulated
        self.is_backtesting = is_backtesting
        self.rest_only = rest_only
        self.ignore_config = ignore_config
        self.is_sandboxed = is_sandboxed
        self.is_collecting = is_collecting
        self.backtesting_files = backtesting_files
        self.exchange_only = exchange_only
        self.exchange_manager = ExchangeManager(config,
                                                exchange_name,
                                                is_simulated=is_simulated,
                                                is_backtesting=is_backtesting,
                                                rest_only=rest_only,
                                                ignore_config=ignore_config,
                                                is_collecting=is_collecting,
                                                exchange_only=exchange_only,
                                                backtesting_files=backtesting_files)

        self.trader: Trader = None

    async def create_basic(self):
        await self.exchange_manager.initialize()
        # add to global exchanges
        Exchanges.instance().add_exchange(self.exchange_manager)

    async def create(self, trading_tentacles_path=CONFIG_TRADING_FILE_PATH):
        await self.exchange_manager.initialize()

        # set sandbox mode
        if not self.is_backtesting:
            self.exchange_manager.exchange.client.setSandboxMode(self.is_sandboxed)

        if not self.is_simulated:
            self.trader = Trader(self.config, self.exchange_manager)
        else:
            self.trader = TraderSimulator(self.config, self.exchange_manager)

        try:
            # check traders activation
            if not is_trader_enabled(self.config) and not is_trader_simulator_enabled(self.config):
                raise ValueError(f"No trader simulator nor real trader activated on {self.exchange_manager.exchange.name}")

            # initialize trader
            await self.trader.initialize()
            self.exchange_manager.trader = self.trader

            init_trading_mode_config(self.config, trading_tentacles_path)
            await create_trading_mode(self.config, self.exchange_manager)

            # add to global exchanges
            Exchanges.instance().add_exchange(self.exchange_manager)
        except Exception as e:
            self.logger.error(f"An error occurred when creating trader or initializing trading mode : ")
            raise e
