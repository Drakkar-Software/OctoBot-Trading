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
import trading_backend.exchanges

from tests import event_loop
import octobot_commons.constants as commons_constants
import octobot_commons.configuration as commons_configuration
import octobot_trading.exchanges as exchanges

pytestmark = pytest.mark.asyncio


@pytest.fixture
def tentacles_setup_config():
    setup_config = mock.Mock()
    setup_config.is_tentacle_activated = mock.Mock(return_value=True)
    setup_config.get_config_folder = mock.Mock(return_value="")
    return setup_config


@pytest.fixture()
def exchange_config():
    return {
        commons_constants.CONFIG_EXCHANGE_KEY: commons_configuration.encrypt("01234").decode(),
        commons_constants.CONFIG_EXCHANGE_SECRET: commons_configuration.encrypt("012345").decode()
    }


async def test_is_compatible_account_with_checked_exchange(exchange_config, tentacles_setup_config):
    with mock.patch.object(trading_backend.exchanges.Huobi, "is_valid_account",
                           mock.AsyncMock(return_value=(True, None))) as is_valid_account_mock:
        compatible, auth, error = await exchanges.is_compatible_account("huobi", exchange_config,
                                                                        tentacles_setup_config, False)
        assert compatible is True
        assert auth is True
        assert error is None
        is_valid_account_mock.assert_called_once()
    with mock.patch.object(trading_backend.exchanges.Huobi, "is_valid_account",
                           mock.AsyncMock(return_value=(False, "plop"))) as is_valid_account_mock:
        compatible, auth, error = await exchanges.is_compatible_account("huobi", exchange_config,
                                                                        tentacles_setup_config, False)
        # still True as on spot trading
        assert compatible is True
        assert auth is True
        assert error is None
        is_valid_account_mock.assert_called_once()
    exchange_config[commons_constants.CONFIG_EXCHANGE_TYPE] = commons_constants.CONFIG_EXCHANGE_FUTURE
    with mock.patch.object(trading_backend.exchanges.Huobi, "is_valid_account",
                           mock.AsyncMock(return_value=(False, "plop"))) as is_valid_account_mock:
        compatible, auth, error = await exchanges.is_compatible_account("huobi", exchange_config,
                                                                        tentacles_setup_config, False)
        assert compatible is False
        assert auth is True
        assert "plop" in error and len(error) > len("plop")
        is_valid_account_mock.assert_called_once()


def test_get_partners_explanation_message():
    assert ".info" in exchanges.get_partners_explanation_message()


def test_log_time_sync_error():
    logger = mock.Mock()
    exchanges.log_time_sync_error(logger, "exchange_name", "error", "details")
    args = logger.error.call_args[0][0]
    assert "exchange_name".capitalize() in args
    assert "error" in args
    assert "details" in args
    assert ".info" in args


async def test_is_compatible_account_with_unchecked_exchange(exchange_config, tentacles_setup_config):
    compatible, auth, error = await exchanges.is_compatible_account("hitbtc", exchange_config, tentacles_setup_config,
                                                                    False)
    assert compatible is False
    assert auth is False
    assert isinstance(error, str)
    exchange_config[commons_constants.CONFIG_EXCHANGE_TYPE] = commons_constants.CONFIG_EXCHANGE_FUTURE
    with mock.patch.object(trading_backend.exchanges.Exchange, "is_valid_account",
                           mock.AsyncMock(return_value=(True, "plop"))) as is_valid_account_mock:
        compatible, auth, error = await exchanges.is_compatible_account("hitbtc", exchange_config,
                                                                        tentacles_setup_config, False)
        assert compatible is True
        assert auth is True
        assert "plop" in error and len(error) > len("plop")
        is_valid_account_mock.assert_called_once()
    with mock.patch.object(trading_backend.exchanges.Exchange, "is_valid_account",
                           mock.AsyncMock(side_effect=trading_backend.ExchangeAuthError)) as is_valid_account_mock:
        compatible, auth, error = await exchanges.is_compatible_account("hitbtc", exchange_config,
                                                                        tentacles_setup_config, False)
        assert compatible is False
        assert auth is False
        assert "authentication" in error and len(error) > len("authentication")
        is_valid_account_mock.assert_called_once()
