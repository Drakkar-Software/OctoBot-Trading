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
from math import isnan

from octobot_trading.data_manager.funding_manager import FundingManager
from tests.util.random_numbers import random_timestamp, random_funding_rate

pytestmark = pytest.mark.asyncio


@pytest.fixture()
async def funding_manager():
    fund_manager = FundingManager()
    await fund_manager.initialize()
    return fund_manager


async def test_init(funding_manager):
    assert funding_manager.next_updated == 0
    assert funding_manager.last_updated == 0
    assert isnan(funding_manager.funding_rate)


async def test_reset_funding(funding_manager):
    funding_manager.next_updated = random_timestamp()
    funding_manager.last_updated = random_timestamp()
    funding_manager.funding_rate = random_funding_rate()
    funding_manager.reset_funding()
    assert funding_manager.next_updated == 0
    assert funding_manager.last_updated == 0
    assert isnan(funding_manager.funding_rate)


async def test_funding_update(funding_manager):
    last_updated = random_timestamp()
    next_updated = random_timestamp(last_updated)
    funding_rate = random_funding_rate()
    funding_manager.funding_update(funding_rate, next_updated, last_updated)
    assert funding_manager.next_updated == next_updated
    assert funding_manager.last_updated == last_updated
    assert funding_manager.funding_rate == funding_rate
