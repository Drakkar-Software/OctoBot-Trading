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

from tests.util.random_numbers import random_quantity, random_price
from tests.exchanges import backtesting_trader, backtesting_config, backtesting_exchange_manager, fake_backtesting

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_init_profitability(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_profitability = exchange_manager.exchange_personal_data.portfolio_manager.portfolio_profitability
    assert portfolio_profitability.profitability == 0
    assert portfolio_profitability.profitability_percent == 0
    assert portfolio_profitability.profitability_diff == 0
    assert portfolio_profitability.market_profitability_percent == 0
    assert portfolio_profitability.initial_portfolio_current_profitability == 0
    assert portfolio_profitability.portfolio_origin_value == 0
    assert portfolio_profitability.portfolio_current_value == 0


async def test_simple_handle_balance_update(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_profitability = exchange_manager.exchange_personal_data.portfolio_manager.portfolio_profitability

    # set the original values
    await portfolio_profitability.handle_balance_update({})
    assert portfolio_profitability.profitability == 0
    assert portfolio_profitability.profitability_percent == 0
    assert portfolio_profitability.profitability_diff == 0
    assert portfolio_profitability.portfolio_origin_value == 10
    assert portfolio_profitability.portfolio_current_value == 10

    new_balance = update_portfolio_balance({
        'BTC': {'available': 20, 'total': 20},
        'USDT': {'available': 1000, 'total': 1000}
    }, exchange_manager)
    await portfolio_profitability.handle_balance_update(new_balance)
    assert portfolio_profitability.profitability == 10
    assert portfolio_profitability.profitability_percent == 100
    assert portfolio_profitability.profitability_diff == 100
    assert portfolio_profitability.portfolio_origin_value == 10
    assert portfolio_profitability.portfolio_current_value == 20


async def test_random_quantity_handle_balance_update(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_profitability = exchange_manager.exchange_personal_data.portfolio_manager.portfolio_profitability
    original_symbol_quantity = 10

    # set the original values
    await portfolio_profitability.handle_balance_update({})
    assert portfolio_profitability.profitability == 0
    assert portfolio_profitability.profitability_percent == 0
    assert portfolio_profitability.profitability_diff == 0
    assert portfolio_profitability.portfolio_origin_value == original_symbol_quantity
    assert portfolio_profitability.portfolio_current_value == original_symbol_quantity

    new_btc_available = random_quantity(max_value=15)  # shouldn't impact profitability
    new_btc_total = random_quantity(min_value=new_btc_available, max_value=15)
    new_prof_percent = (100 * new_btc_total / original_symbol_quantity) - 100
    new_balance = update_portfolio_balance({'BTC': {'available': new_btc_available, 'total': new_btc_total}},
                                           exchange_manager)
    await portfolio_profitability.handle_balance_update(new_balance)
    assert portfolio_profitability.profitability == new_btc_total - original_symbol_quantity
    assert portfolio_profitability.profitability_percent == new_prof_percent
    assert portfolio_profitability.profitability_diff == new_prof_percent - 0
    assert portfolio_profitability.portfolio_origin_value == original_symbol_quantity
    assert portfolio_profitability.portfolio_current_value == new_btc_total

    new_btc_total_2 = random_quantity(min_value=new_btc_available, max_value=12)
    new_prof_percent_2 = (100 * new_btc_total_2 / original_symbol_quantity) - 100
    new_balance = update_portfolio_balance({'BTC': {'total': new_btc_total_2}}, exchange_manager)
    await portfolio_profitability.handle_balance_update(new_balance)
    assert portfolio_profitability.profitability == new_btc_total_2 - original_symbol_quantity
    assert portfolio_profitability.profitability_percent == new_prof_percent_2
    assert portfolio_profitability.profitability_diff == new_prof_percent_2 - new_prof_percent
    assert portfolio_profitability.portfolio_origin_value == original_symbol_quantity
    assert portfolio_profitability.portfolio_current_value == new_btc_total_2


async def test_get_current_crypto_currencies_values(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_profitability = exchange_manager.exchange_personal_data.portfolio_manager.portfolio_profitability

    assert await portfolio_profitability.get_current_crypto_currencies_values() == {'BTC': 1, 'USDT': 0}
    new_balance = update_portfolio_balance({
        'BTC': {'available': random_quantity(), 'total': random_quantity()},
        'ETH': {'available': random_quantity(), 'total': random_quantity()},
        'XRP': {'available': random_quantity(), 'total': random_quantity()},
        'NANO': {'available': random_quantity(), 'total': random_quantity()},
        'XLM': {'available': random_quantity(), 'total': random_quantity()},
        'USDT': {'available': random_quantity(), 'total': random_quantity()}
    }, exchange_manager)
    await portfolio_profitability.handle_balance_update(new_balance)

    assert await portfolio_profitability.get_current_crypto_currencies_values() == {
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
        portfolio_profitability.missing_currency_data_in_exchange.remove("XRP")
        await portfolio_profitability.handle_mark_price_update("XRP/BTC", 0.005)
        exchange_manager.client_symbols.append("NANO/BTC")
        portfolio_profitability.missing_currency_data_in_exchange.remove("NANO")
        await portfolio_profitability.handle_mark_price_update("NANO/BTC", 0.05)
        exchange_manager.client_symbols.append("BTC/USDT")

        assert await portfolio_profitability.get_current_crypto_currencies_values() == {
            'BTC': 1,
            'ETH': 0,
            'XRP': 0.005,
            'NANO': 0.05,
            'XLM': 0,
            'USDT': 0
        }
        xlm_btc_price = random_price(max_value=0.05)
        portfolio_profitability.missing_currency_data_in_exchange.remove("XLM")
        await portfolio_profitability.handle_mark_price_update("XLM/BTC", xlm_btc_price)
        assert await portfolio_profitability.get_current_crypto_currencies_values() == {
            'BTC': 1,
            'ETH': 0,
            'XRP': 0.005,
            'NANO': 0.05,
            'XLM': xlm_btc_price,
            'USDT': 0
        }
        usdt_btc_price = random_price(max_value=0.01)
        portfolio_profitability.missing_currency_data_in_exchange.remove("USDT")
        await portfolio_profitability.handle_mark_price_update("BTC/USDT", usdt_btc_price)
        assert await portfolio_profitability.get_current_crypto_currencies_values() == {
            'BTC': 1,
            'ETH': 0,
            'XRP': 0.005,
            'NANO': 0.05,
            'XLM': xlm_btc_price,
            'USDT': 1 / usdt_btc_price
        }
        eth_btc_price = random_price(max_value=1)
        exchange_manager.client_symbols.append("ETH/BTC")
        portfolio_profitability.missing_currency_data_in_exchange.remove("ETH")
        await portfolio_profitability.handle_mark_price_update("ETH/BTC", eth_btc_price)
        assert await portfolio_profitability.get_current_crypto_currencies_values() == {
            'BTC': 1,
            'ETH': eth_btc_price,
            'XRP': 0.005,
            'NANO': 0.05,
            'XLM': xlm_btc_price,
            'USDT': 1 / usdt_btc_price
        }


async def test_get_current_holdings_values(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_profitability = exchange_manager.exchange_personal_data.portfolio_manager.portfolio_profitability
    exchange_manager.client_symbols.append("ETH/BTC")
    new_balance = update_portfolio_balance({
        'BTC': {'available': 10, 'total': 10},
        'ETH': {'available': 100, 'total': 100},
        'XRP': {'available': 10000, 'total': 10000},
        'USDT': {'available': 1000, 'total': 1000}
    }, exchange_manager)
    await portfolio_profitability.handle_balance_update(new_balance)
    assert await portfolio_profitability.get_current_holdings_values() == {
        'BTC': 10,
        'ETH': 0,
        'XRP': 0,
        'USDT': 0
    }
    await portfolio_profitability.handle_mark_price_update("ETH/BTC", 50)
    assert await portfolio_profitability.get_current_holdings_values() == {
        'BTC': 10,
        'ETH': 5000,
        'XRP': 0,
        'USDT': 0
    }
    await portfolio_profitability.handle_mark_price_update("XRP/USDT", 2.5)
    assert await portfolio_profitability.get_current_holdings_values() == {
        'BTC': 10,
        'ETH': 5000,
        'XRP': 0,
        'USDT': 0
    }
    await portfolio_profitability.handle_mark_price_update("XRP/BTC", 0.00001)
    assert await portfolio_profitability.get_current_holdings_values() == {
        'BTC': 10,
        'ETH': 5000,
        'XRP': 0,
        'USDT': 0
    }
    if not os.getenv('CYTHON_IGNORE'):
        exchange_manager.client_symbols.append("XRP/BTC")
        portfolio_profitability.missing_currency_data_in_exchange.remove("XRP")
        await portfolio_profitability.handle_mark_price_update("XRP/BTC", 0.00001)
        assert await portfolio_profitability.get_current_holdings_values() == {
            'BTC': 10,
            'ETH': 5000,
            'XRP': 0.1,
            'USDT': 0
        }
        exchange_manager.client_symbols.append("BTC/USDT")
        portfolio_profitability.missing_currency_data_in_exchange.remove("USDT")
        await portfolio_profitability.handle_mark_price_update("BTC/USDT", 5000)
        assert await portfolio_profitability.get_current_holdings_values() == {
            'BTC': 10,
            'ETH': 5000,
            'XRP': 0.1,
            'USDT': 0.2
        }


def update_portfolio_balance(new_balance, exchange_manager):
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio.portfolio = new_balance
    return new_balance
