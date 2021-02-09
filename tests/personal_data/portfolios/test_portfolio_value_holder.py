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
import os
import pytest

from tests.personal_data.portfolios import update_portfolio_balance
from tests.test_utils.random_numbers import random_quantity, random_price

from tests.exchanges import backtesting_trader, backtesting_config, backtesting_exchange_manager, fake_backtesting
from tests import event_loop

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_get_current_crypto_currencies_values(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder

    assert portfolio_value_holder.get_current_crypto_currencies_values() == {'BTC': 1, 'USDT': 0}
    update_portfolio_balance({
        'BTC': {'available': random_quantity(), 'total': random_quantity()},
        'ETH': {'available': random_quantity(), 'total': random_quantity()},
        'XRP': {'available': random_quantity(), 'total': random_quantity()},
        'NANO': {'available': random_quantity(), 'total': random_quantity()},
        'XLM': {'available': random_quantity(), 'total': random_quantity()},
        'USDT': {'available': random_quantity(), 'total': random_quantity()}
    }, exchange_manager)
    await portfolio_manager.handle_balance_updated()

    assert portfolio_value_holder.get_current_crypto_currencies_values() == {
        'BTC': 1,
        'ETH': 0,
        'XRP': 0,
        'NANO': 0,
        'XLM': 0,
        'USDT': 0
    }

    exchange_manager.client_symbols.append("XLM/BTC")
    exchange_manager.client_symbols.append("XRP/BTC")
    if not os.getenv('CYTHON_IGNORE'):
        portfolio_value_holder.missing_currency_data_in_exchange.remove("XRP")
        await portfolio_manager.handle_mark_price_update("XRP/BTC", 0.005)
        exchange_manager.client_symbols.append("NANO/BTC")
        portfolio_value_holder.missing_currency_data_in_exchange.remove("NANO")
        await portfolio_manager.handle_mark_price_update("NANO/BTC", 0.05)
        exchange_manager.client_symbols.append("BTC/USDT")

        assert portfolio_value_holder.get_current_crypto_currencies_values() == {
            'BTC': 1,
            'ETH': 0,
            'XRP': 0.005,
            'NANO': 0.05,
            'XLM': 0,
            'USDT': 0
        }
        xlm_btc_price = random_price(max_value=0.05)
        portfolio_value_holder.missing_currency_data_in_exchange.remove("XLM")
        await portfolio_manager.handle_mark_price_update("XLM/BTC", xlm_btc_price)
        assert portfolio_value_holder.get_current_crypto_currencies_values() == {
            'BTC': 1,
            'ETH': 0,
            'XRP': 0.005,
            'NANO': 0.05,
            'XLM': xlm_btc_price,
            'USDT': 0
        }
        usdt_btc_price = random_price(max_value=0.01)
        portfolio_value_holder.missing_currency_data_in_exchange.remove("USDT")
        await portfolio_manager.handle_mark_price_update("BTC/USDT", usdt_btc_price)
        assert portfolio_value_holder.get_current_crypto_currencies_values() == {
            'BTC': 1,
            'ETH': 0,
            'XRP': 0.005,
            'NANO': 0.05,
            'XLM': xlm_btc_price,
            'USDT': 1 / usdt_btc_price
        }
        eth_btc_price = random_price(max_value=1)
        exchange_manager.client_symbols.append("ETH/BTC")
        portfolio_value_holder.missing_currency_data_in_exchange.remove("ETH")
        await portfolio_manager.handle_mark_price_update("ETH/BTC", eth_btc_price)
        assert portfolio_value_holder.get_current_crypto_currencies_values() == {
            'BTC': 1,
            'ETH': eth_btc_price,
            'XRP': 0.005,
            'NANO': 0.05,
            'XLM': xlm_btc_price,
            'USDT': 1 / usdt_btc_price
        }


async def test_get_current_holdings_values(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder

    exchange_manager.client_symbols.append("ETH/BTC")
    update_portfolio_balance({
        'BTC': {'available': 10, 'total': 10},
        'ETH': {'available': 100, 'total': 100},
        'XRP': {'available': 10000, 'total': 10000},
        'USDT': {'available': 1000, 'total': 1000}
    }, exchange_manager)
    await portfolio_manager.handle_balance_updated()
    assert portfolio_value_holder.get_current_holdings_values() == {
        'BTC': 10,
        'ETH': 0,
        'XRP': 0,
        'USDT': 0
    }
    await portfolio_manager.handle_mark_price_update("ETH/BTC", 50)
    assert portfolio_value_holder.get_current_holdings_values() == {
        'BTC': 10,
        'ETH': 5000,
        'XRP': 0,
        'USDT': 0
    }
    await portfolio_manager.handle_mark_price_update("XRP/USDT", 2.5)
    assert portfolio_value_holder.get_current_holdings_values() == {
        'BTC': 10,
        'ETH': 5000,
        'XRP': 0,
        'USDT': 0
    }
    await portfolio_manager.handle_mark_price_update("XRP/BTC", 0.00001)
    assert portfolio_value_holder.get_current_holdings_values() == {
        'BTC': 10,
        'ETH': 5000,
        'XRP': 0,
        'USDT': 0
    }
    if not os.getenv('CYTHON_IGNORE'):
        exchange_manager.client_symbols.append("XRP/BTC")
        portfolio_value_holder.missing_currency_data_in_exchange.remove("XRP")
        await portfolio_manager.handle_mark_price_update("XRP/BTC", 0.00001)
        assert portfolio_value_holder.get_current_holdings_values() == {
            'BTC': 10,
            'ETH': 5000,
            'XRP': 0.1,
            'USDT': 0
        }
        exchange_manager.client_symbols.append("BTC/USDT")
        portfolio_value_holder.missing_currency_data_in_exchange.remove("USDT")
        await portfolio_manager.handle_mark_price_update("BTC/USDT", 5000)
        assert portfolio_value_holder.get_current_holdings_values() == {
            'BTC': 10,
            'ETH': 5000,
            'XRP': 0.1,
            'USDT': 0.2
        }


async def test_get_origin_portfolio_current_value(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder

    await portfolio_manager.handle_profitability_recalculation(True)
    assert portfolio_value_holder.get_origin_portfolio_current_value() == 10


async def test_get_origin_portfolio_current_value_with_different_reference_market(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder

    portfolio_manager.reference_market = "USDT"
    await portfolio_manager.handle_profitability_recalculation(True)
    assert portfolio_value_holder.get_origin_portfolio_current_value() == 1000


async def test_update_origin_crypto_currencies_values(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder

    assert portfolio_value_holder.update_origin_crypto_currencies_values("ETH/BTC", 0.1) is True
    assert portfolio_value_holder.origin_crypto_currencies_values["ETH"] == 0.1
    assert portfolio_value_holder.last_prices_by_trading_pair["ETH/BTC"] == 0.1

    assert portfolio_value_holder.update_origin_crypto_currencies_values("BTC/USDT", 100) is True
    assert portfolio_value_holder.origin_crypto_currencies_values["USDT"] == 1 / 100
    assert portfolio_value_holder.last_prices_by_trading_pair["BTC/USDT"] == 100
