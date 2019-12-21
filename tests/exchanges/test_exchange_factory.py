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
from shutil import copyfile

import pytest

from octobot_commons.constants import CONFIG_TRADING_FILE, TENTACLES_TRADING_PATH, TENTACLES_PATH
from octobot_commons.errors import ConfigTradingError
from octobot_commons.tests.test_config import load_test_config, TEST_CONFIG_FOLDER
from octobot_trading.api.exchange import create_new_exchange
from octobot_trading.exchanges.exchanges import Exchanges
from tests.util import reset_exchanges_list, delete_all_channels

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

TESTS_FOLDER = "tests"
TESTS_STATIC_FOLDER = os.path.join(TESTS_FOLDER, "static")
TEST_TRADING_TENTACLES_PATH = os.path.join(TESTS_FOLDER, TENTACLES_PATH, TENTACLES_TRADING_PATH)
TEST_TRADING_TENTACLES_CONFIG_PATH = os.path.join(TEST_TRADING_TENTACLES_PATH, CONFIG_TRADING_FILE)


def create_test_tentacles_config():
    if not os.path.exists(TEST_TRADING_TENTACLES_PATH):
        os.makedirs(TEST_TRADING_TENTACLES_PATH)
        copyfile(os.path.join(TEST_CONFIG_FOLDER, CONFIG_TRADING_FILE), TEST_TRADING_TENTACLES_CONFIG_PATH)


def remove_test_tentacles_config():
    if not os.path.exists(TEST_TRADING_TENTACLES_PATH):
        os.removedirs(TEST_TRADING_TENTACLES_PATH)


class TestExchangeFactory:
    EXCHANGE_NAME = "binance"

    @staticmethod
    async def init_default(simulated=True, rest_only=True, backtesting=False, sandboxed=False):
        reset_exchanges_list()
        delete_all_channels(TestExchangeFactory.EXCHANGE_NAME)

        config = load_test_config()

        exchange_factory = create_new_exchange(config,
                                               TestExchangeFactory.EXCHANGE_NAME,
                                               is_simulated=simulated,
                                               is_rest_only=rest_only,
                                               is_backtesting=backtesting,
                                               is_sandboxed=sandboxed)

        return config, exchange_factory

    async def test_create_without_trading_config(self):
        config, exchange_factory = await self.init_default()

        with pytest.raises(ConfigTradingError):
            await exchange_factory.create()
        await exchange_factory.exchange_manager.stop()

    async def test_create_without_activated_trading_mode_config(self):
        create_test_tentacles_config()
        config, exchange_factory = await self.init_default()

        with pytest.raises(ConfigTradingError):
            await exchange_factory.create()

        remove_test_tentacles_config()
        await exchange_factory.exchange_manager.stop()

    async def test_create(self):
        create_test_tentacles_config()

        config, exchange_factory = await self.init_default()

        # TODO wait for tentacles installation
        # await exchange_factory.create(trading_tentacles_path=TEST_TRADING_TENTACLES_CONFIG_PATH)
        #
        # assert exchange_factory.exchange_manager is not None
        # assert exchange_factory.exchange_name is TestExchangeFactory.EXCHANGE_NAME
        #
        # assert exchange_factory.exchange_manager.config is config
        #
        # assert Exchanges.instance().get_exchange(TestExchangeFactory.EXCHANGE_NAME)

        remove_test_tentacles_config()
        await exchange_factory.exchange_manager.stop()

    async def test_create_basic(self):
        config, exchange_factory = await self.init_default()
        await exchange_factory.create_basic()

        assert exchange_factory.exchange_manager is not None
        assert exchange_factory.exchange_name is TestExchangeFactory.EXCHANGE_NAME

        assert exchange_factory.exchange_manager.config is config

        with pytest.raises(KeyError):
            assert Exchanges.instance().get_exchange(TestExchangeFactory.EXCHANGE_NAME)
        await exchange_factory.exchange_manager.stop()
