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
import pytest

from octobot_commons.tests.test_config import load_test_config
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.exchanges.exchanges import Exchanges

pytestmark = pytest.mark.asyncio


class TestExchanges:
    @staticmethod
    async def init_default():
        return load_test_config()
