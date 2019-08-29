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

from octobot_trading.api.modes import create_trading_mode, init_trading_mode_config
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.traders.trader import Trader
from octobot_trading.traders.trader_simulator import TraderSimulator


class ExchangeFactory:
    def __init__(self, config, exchange_name,
                 is_simulated=False,
                 is_backtesting=False,
                 rest_only=False,
                 is_sandboxed=False):
        self.logger = get_logger(self.__class__.__name__)
        self.config = config
        self.exchange_name = exchange_name
        self.is_simulated = is_simulated
        self.is_backtesting = is_backtesting
        self.rest_only = rest_only
        self.is_sandboxed = is_sandboxed
        self.exchange_manager = ExchangeManager(config,
                                                exchange_name,
                                                is_simulated=is_simulated,
                                                is_backtesting=is_backtesting,
                                                rest_only=rest_only)

        self.trader: Trader = None

    async def create(self):
        await self.exchange_manager.initialize()

        # set sandbox mode
        self.exchange_manager.exchange.client.setSandboxMode(self.is_sandboxed)

        self.trader = Trader(self.config, self.exchange_manager) if not self.is_simulated \
            else TraderSimulator(self.config, self.exchange_manager)

        try:
            # check traders activation
            if not self.trader.enabled(self.config):
                raise ValueError(f"No trader simulator nor real trader activated on {self.exchange_manager.exchange.name}")

            # initialize trader
            await self.trader.initialize()
            self.exchange_manager.trader = self.trader

            init_trading_mode_config(self.config)
            await create_trading_mode(self.config, self.exchange_manager)
        except Exception as e:
            self.logger.error(f"An error occurred when creating trader or initializing trading mode : ")
            raise e
