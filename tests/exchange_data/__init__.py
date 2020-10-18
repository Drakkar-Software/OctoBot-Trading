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
import octobot_trading.exchange_data as exchange_data


@pytest.fixture()
def price_events_manager(event_loop):
    return exchange_data.PriceEventsManager()


@pytest.fixture()
def prices_manager(event_loop, backtesting_exchange_manager):
    return exchange_data.PricesManager(backtesting_exchange_manager)


@pytest.fixture()
def recent_trades_manager(event_loop):
    return exchange_data.RecentTradesManager()
