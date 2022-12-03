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
import octobot_trading.api as api
import octobot_trading.exchanges as exchanges

from tests.exchanges import exchange_manager
from tests import event_loop


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_build_trading_modes_if_required(exchange_manager):
    builder = exchanges.ExchangeBuilder({}, "binanceus")
    builder.exchange_manager = exchange_manager

    # no set trader: no trading mode creation attempt
    assert builder.exchange_manager.trader is None
    await builder._build_trading_modes_if_required(None)
    assert builder.exchange_manager.trader is None

    # with trader simulator: will attempt to create a trading mode and fail (because of the None arg)
    builder.is_simulated()
    with pytest.raises(AttributeError):
        await builder._build_trading_modes_if_required(None)


async def test_build_collector_exchange(exchange_manager):
    new_exchange_manager = await api.create_exchange_builder(exchange_manager.config, exchange_manager.exchange_name) \
        .is_simulated() \
        .is_rest_only() \
        .is_exchange_only() \
        .is_without_auth() \
        .is_ignoring_config() \
        .disable_trading_mode() \
        .use_tentacles_setup_config(exchange_manager.tentacles_setup_config) \
        .build()
    assert new_exchange_manager is not exchange_manager
    assert new_exchange_manager.config is exchange_manager.config
    assert new_exchange_manager.exchange_name == exchange_manager.exchange_name
    assert new_exchange_manager.tentacles_setup_config is exchange_manager.tentacles_setup_config
    await new_exchange_manager.stop()
