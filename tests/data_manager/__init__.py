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
from octobot_trading.data_manager.recent_trades_manager import RecentTradesManager

from octobot_trading.data_manager.prices_manager import PricesManager

from octobot_trading.data_manager.price_events_manager import PriceEventsManager

from tests import event_loop


@pytest.fixture()
def price_events_manager(event_loop):
    return PriceEventsManager()


@pytest.fixture()
def prices_manager(event_loop, backtesting_exchange_manager):
    return PricesManager(backtesting_exchange_manager)


@pytest.fixture()
def recent_trades_manager(event_loop):
    return RecentTradesManager()
