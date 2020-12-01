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
import mock

import octobot_trading.exchanges as exchanges
import octobot_trading.enums as enums
import octobot_commons.tests.test_config as test_config

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


EXCHANGE_NAME = "binance"


@pytest.fixture
def abstract_exchange():
    config = test_config.load_test_config()
    return exchanges.AbstractExchange(config, exchanges.ExchangeManager(config, EXCHANGE_NAME))


async def test_log_order_creation_error(abstract_exchange):
    logger_mock = mock.Mock()
    abstract_exchange.logger = logger_mock
    error = RuntimeError()
    abstract_exchange.log_order_creation_error(error, enums.TraderOrderType.BUY_MARKET, "BTC/USD",
                                               1.0542454, 100.114, 100.114)
    logger_mock.error.assert_called_once()
    assert all(f"{e}" in logger_mock.mock_calls[0].args[0] for e in (enums.TraderOrderType.BUY_MARKET, "BTC/USD",
                                                                     1.0542454, 100.114, 100.114))
    logger_mock.reset_mock()
    abstract_exchange.log_order_creation_error(error, enums.TraderOrderType.BUY_MARKET, "BTC/USD", 0, None, None)
    logger_mock.error.assert_called_once()
    assert all(f"{e}" in logger_mock.mock_calls[0].args[0] for e in (enums.TraderOrderType.BUY_MARKET, "BTC/USD",
                                                                     0, None, None))
    logger_mock.reset_mock()
