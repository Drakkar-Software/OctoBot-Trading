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
from shutil import copyfile

import os

import pytest

from octobot_commons.tests.test_config import load_test_config, TEST_CONFIG_FOLDER
from octobot_tentacles_manager.constants import USER_TENTACLE_CONFIG_PATH, CONFIG_TENTACLES_FILE
from octobot_trading.api.exchange import create_exchange_builder
from octobot_trading.exchanges.exchange_manager import ExchangeManager

pytestmark = pytest.mark.asyncio

TESTS_FOLDER = "tests"
TESTS_STATIC_FOLDER = os.path.join(TESTS_FOLDER, "static")
TEST_TRADING_TENTACLES_CONFIG_PATH = os.path.join(TESTS_FOLDER, USER_TENTACLE_CONFIG_PATH)
TEST_TRADING_TENTACLES_CONFIG_FILE_PATH = os.path.join(TEST_TRADING_TENTACLES_CONFIG_PATH, CONFIG_TENTACLES_FILE)


@pytest.yield_fixture
async def exchange_manager(config=None, exchange_name="binance"):
    exchange_manager_instance = ExchangeManager(config if config is not None else load_test_config(), exchange_name)
    await exchange_manager_instance.initialize()
    yield exchange_manager_instance
    await exchange_manager_instance.stop()


@pytest.yield_fixture
async def create_test_tentacles_config():
    if not os.path.exists(TEST_TRADING_TENTACLES_CONFIG_PATH):
        os.makedirs(TEST_TRADING_TENTACLES_CONFIG_PATH)
        copyfile(os.path.join(TEST_CONFIG_FOLDER, CONFIG_TENTACLES_FILE), TEST_TRADING_TENTACLES_CONFIG_PATH)
    yield TEST_TRADING_TENTACLES_CONFIG_PATH
    if not os.path.exists(TEST_TRADING_TENTACLES_CONFIG_PATH):
        os.removedirs(TEST_TRADING_TENTACLES_CONFIG_PATH)


@pytest.yield_fixture
async def exchange_builder(request):
    config = None
    exchange_name = "binance"
    if hasattr(request, "param"):
        config, exchange_name = request.param

    exchange_builder_instance = create_exchange_builder(config if config is not None else load_test_config(),
                                                        exchange_name).is_simulated().is_rest_only()
    yield exchange_builder_instance
    await exchange_builder_instance.exchange_manager.stop()
