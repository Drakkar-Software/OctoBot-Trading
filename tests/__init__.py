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
import aiohttp
import asyncio
from os import path
import pytest
import requests
from octobot_commons.tests.test_config import load_test_config

from octobot_tentacles_manager.api.installer import install_all_tentacles
from octobot_tentacles_manager.constants import TENTACLES_PATH
from octobot_tentacles_manager.managers.tentacles_setup_manager import TentaclesSetupManager

TENTACLES_LATEST_URL = "https://www.tentacles.octobot.online/repository/tentacles/officials/base/latest.zip"


@pytest.yield_fixture
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def config():
    return load_test_config()


@pytest.yield_fixture
async def install_tentacles():
    def _download_tentacles():
        r = requests.get(TENTACLES_LATEST_URL, stream=True)
        open(_tentacles_local_path(), 'wb').write(r.content)

    def _cleanup(raises=True):
        if path.exists(TENTACLES_PATH):
            TentaclesSetupManager.delete_tentacles_arch(force=True, raises=raises)

    def _tentacles_local_path():
        return path.join("tests", "static", "tentacles.zip")

    if not path.exists(_tentacles_local_path()):
        _download_tentacles()

    _cleanup(False)
    async with aiohttp.ClientSession() as session:
        yield await install_all_tentacles(_tentacles_local_path(), aiohttp_session=session)
    _cleanup()
