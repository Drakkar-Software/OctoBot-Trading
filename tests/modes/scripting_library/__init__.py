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
import decimal

import octobot_trading.modes.scripting_library as scripting_library
import octobot_trading.enums as enums

import tests.personal_data.portfolios as portfolios
import tests.test_utils.random_numbers as random_numbers


@pytest.fixture
def null_context():
    context = scripting_library.Context(
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )
    yield context


@pytest.fixture
async def mock_context(backtesting_trader):
    _, exchange_manager, trader_inst = backtesting_trader
    context = scripting_library.Context(
        mock.Mock(),
        exchange_manager,
        trader_inst,
        mock.Mock(),
        "BTC/USDT",
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
    )
    # init portfolio with 0.5 BTC, 20 ETH and 30000 USDT and only 0.1 available BTC
    portfolios.update_portfolio_balance({
        'BTC': {'available': decimal.Decimal("0.1"), 'total': decimal.Decimal("0.5")},
        'ETH': {'available': decimal.Decimal("20"), 'total': decimal.Decimal("20")},
        'USDT': {'available': decimal.Decimal("30000"), 'total': decimal.Decimal("30000")}
    }, exchange_manager)
    exchange_manager.client_symbols.append("BTC/USDT")
    exchange_manager.client_symbols.append("ETH/USDT")
    exchange_manager.client_symbols.append("ETH/BTC")
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    # init prices with BTC/USDT = 40000, ETH/BTC = 0.1 and ETH/USDT = 4000
    portfolio_manager.portfolio_value_holder.last_prices_by_trading_pair["BTC/USDT"] = decimal.Decimal("40000")
    portfolio_manager.portfolio_value_holder.last_prices_by_trading_pair["ETH/USDT"] = decimal.Decimal("4000")
    portfolio_manager.portfolio_value_holder.last_prices_by_trading_pair["ETH/BTC"] = decimal.Decimal("0.1")
    await portfolio_manager.handle_balance_updated()
    yield context


@pytest.fixture
def symbol_market():
    return {
        enums.ExchangeConstantsMarketStatusColumns.LIMITS.value: {
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT_MIN.value: 0.5,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_AMOUNT_MAX.value: 100,
            },
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST_MIN.value: 1,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_COST_MAX.value: 200
            },
            enums.ExchangeConstantsMarketStatusColumns.LIMITS_PRICE.value: {
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_PRICE_MIN.value: 0.5,
                enums.ExchangeConstantsMarketStatusColumns.LIMITS_PRICE_MAX.value: 50
            },
        },
        enums.ExchangeConstantsMarketStatusColumns.PRECISION.value: {
            enums.ExchangeConstantsMarketStatusColumns.PRECISION_PRICE.value: 8,
            enums.ExchangeConstantsMarketStatusColumns.PRECISION_AMOUNT.value: 8
        }
    }