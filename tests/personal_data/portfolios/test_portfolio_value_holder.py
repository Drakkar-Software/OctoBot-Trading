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
import decimal
import os
import pytest

import octobot_trading.constants as constants
from tests.personal_data.portfolios import update_portfolio_balance
from tests.test_utils.random_numbers import decimal_random_quantity, random_price

from tests.exchanges import backtesting_trader, backtesting_config, backtesting_exchange_manager, fake_backtesting
from tests import event_loop

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_get_current_crypto_currencies_values(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder

    assert portfolio_value_holder.get_current_crypto_currencies_values() == {'BTC': constants.ONE, 'USDT': constants.ZERO}
    update_portfolio_balance({
        'BTC': {'available': decimal_random_quantity(), 'total': decimal_random_quantity()},
        'ETH': {'available': decimal_random_quantity(), 'total': decimal_random_quantity()},
        'XRP': {'available': decimal_random_quantity(), 'total': decimal_random_quantity()},
        'NANO': {'available': decimal_random_quantity(), 'total': decimal_random_quantity()},
        'XLM': {'available': decimal_random_quantity(), 'total': decimal_random_quantity()},
        'USDT': {'available': decimal_random_quantity(), 'total': decimal_random_quantity()}
    }, exchange_manager)
    await portfolio_manager.handle_balance_updated()

    assert portfolio_value_holder.get_current_crypto_currencies_values() == {
        'BTC': constants.ONE,
        'ETH': constants.ZERO,
        'XRP': constants.ZERO,
        'NANO': constants.ZERO,
        'XLM': constants.ZERO,
        'USDT': constants.ZERO
    }

    exchange_manager.client_symbols.append("XLM/BTC")
    exchange_manager.client_symbols.append("XRP/BTC")
    if not os.getenv('CYTHON_IGNORE'):
        portfolio_value_holder.missing_currency_data_in_exchange.remove("XRP")
        await portfolio_manager.handle_mark_price_update("XRP/BTC", decimal.Decimal("0.005"))
        exchange_manager.client_symbols.append("NANO/BTC")
        portfolio_value_holder.missing_currency_data_in_exchange.remove("NANO")
        await portfolio_manager.handle_mark_price_update("NANO/BTC", decimal.Decimal("0.05"))
        exchange_manager.client_symbols.append("BTC/USDT")

        assert portfolio_value_holder.get_current_crypto_currencies_values() == {
            'BTC': constants.ONE,
            'ETH': constants.ZERO,
            'XRP': decimal.Decimal("0.005"),
            'NANO': decimal.Decimal("0.05"),
            'XLM': constants.ZERO,
            'USDT': constants.ZERO
        }
        xlm_btc_price = random_price(max_value=0.05)
        portfolio_value_holder.missing_currency_data_in_exchange.remove("XLM")
        await portfolio_manager.handle_mark_price_update("XLM/BTC", xlm_btc_price)
        assert portfolio_value_holder.get_current_crypto_currencies_values() == {
            'BTC': constants.ONE,
            'ETH': constants.ZERO,
            'XRP': decimal.Decimal("0.005"),
            'NANO': decimal.Decimal("0.05"),
            'XLM': decimal.Decimal(str(xlm_btc_price)),
            'USDT': constants.ZERO
        }
        usdt_btc_price = random_price(max_value=0.01)
        portfolio_value_holder.missing_currency_data_in_exchange.remove("USDT")
        await portfolio_manager.handle_mark_price_update("BTC/USDT", usdt_btc_price)
        assert portfolio_value_holder.get_current_crypto_currencies_values() == {
            'BTC': constants.ONE,
            'ETH': constants.ZERO,
            'XRP': decimal.Decimal("0.005"),
            'NANO': decimal.Decimal("0.05"),
            'XLM': decimal.Decimal(str(xlm_btc_price)),
            'USDT': constants.ONE / decimal.Decimal(str(usdt_btc_price))
        }
        eth_btc_price = random_price(max_value=1)
        exchange_manager.client_symbols.append("ETH/BTC")
        portfolio_value_holder.missing_currency_data_in_exchange.remove("ETH")
        await portfolio_manager.handle_mark_price_update("ETH/BTC", eth_btc_price)
        assert portfolio_value_holder.get_current_crypto_currencies_values() == {
            'BTC': constants.ONE,
            'ETH': decimal.Decimal(str(eth_btc_price)),
            'XRP': decimal.Decimal("0.005"),
            'NANO': decimal.Decimal("0.05"),
            'XLM': decimal.Decimal(str(xlm_btc_price)),
            'USDT': constants.ONE / decimal.Decimal(str(usdt_btc_price))
        }


async def test_get_current_holdings_values(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder

    exchange_manager.client_symbols.append("ETH/BTC")
    update_portfolio_balance({
        'BTC': {'available': decimal.Decimal("10"), 'total': decimal.Decimal("10")},
        'ETH': {'available': decimal.Decimal("100"), 'total': decimal.Decimal("100")},
        'XRP': {'available': decimal.Decimal("10000"), 'total': decimal.Decimal("10000")},
        'USDT': {'available': decimal.Decimal("1000"), 'total': decimal.Decimal("1000")}
    }, exchange_manager)
    await portfolio_manager.handle_balance_updated()
    assert portfolio_value_holder.get_current_holdings_values() == {
        'BTC': decimal.Decimal("10"),
        'ETH': constants.ZERO,
        'XRP': constants.ZERO,
        'USDT': constants.ZERO
    }
    await portfolio_manager.handle_mark_price_update("ETH/BTC", 50)
    assert portfolio_value_holder.get_current_holdings_values() == {
        'BTC': decimal.Decimal("10"),
        'ETH': decimal.Decimal("5000"),
        'XRP': constants.ZERO,
        'USDT': constants.ZERO
    }
    await portfolio_manager.handle_mark_price_update("XRP/USDT", 2.5)
    assert portfolio_value_holder.get_current_holdings_values() == {
        'BTC': decimal.Decimal("10"),
        'ETH': decimal.Decimal("5000"),
        'XRP': constants.ZERO,
        'USDT': constants.ZERO
    }
    await portfolio_manager.handle_mark_price_update("XRP/BTC", 0.00001)
    assert portfolio_value_holder.get_current_holdings_values() == {
        'BTC': decimal.Decimal("10"),
        'ETH': decimal.Decimal("5000"),
        'XRP': constants.ZERO,
        'USDT': constants.ZERO
    }
    if not os.getenv('CYTHON_IGNORE'):
        exchange_manager.client_symbols.append("XRP/BTC")
        portfolio_value_holder.missing_currency_data_in_exchange.remove("XRP")
        await portfolio_manager.handle_mark_price_update("XRP/BTC", 0.00001)
        assert portfolio_value_holder.get_current_holdings_values() == {
            'BTC': decimal.Decimal(10),
            'ETH': decimal.Decimal(5000),
            'XRP': decimal.Decimal(str(0.1)),
            'USDT': constants.ZERO
        }
        exchange_manager.client_symbols.append("BTC/USDT")
        portfolio_value_holder.missing_currency_data_in_exchange.remove("USDT")
        await portfolio_manager.handle_mark_price_update("BTC/USDT", 5000)
        assert portfolio_value_holder.get_current_holdings_values() == {
            'BTC': decimal.Decimal(10),
            'ETH': decimal.Decimal(5000),
            'XRP': decimal.Decimal(str(0.1)),
            'USDT': decimal.Decimal(str(0.2))
        }


async def test_get_origin_portfolio_current_value(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder

    await portfolio_manager.handle_profitability_recalculation(True)
    assert portfolio_value_holder.get_origin_portfolio_current_value() == decimal.Decimal(str(10))


async def test_get_origin_portfolio_current_value_with_different_reference_market(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder

    portfolio_manager.reference_market = "USDT"
    await portfolio_manager.handle_profitability_recalculation(True)
    assert portfolio_value_holder.get_origin_portfolio_current_value() == decimal.Decimal(str(1000))


async def test_update_origin_crypto_currencies_values(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder

    assert portfolio_value_holder.update_origin_crypto_currencies_values("ETH/BTC", decimal.Decimal(str(0.1))) is True
    assert portfolio_value_holder.origin_crypto_currencies_values["ETH"] == decimal.Decimal(str(0.1))
    assert portfolio_value_holder.last_prices_by_trading_pair["ETH/BTC"] == decimal.Decimal(str(0.1))

    assert portfolio_value_holder.update_origin_crypto_currencies_values("BTC/USDT", decimal.Decimal(str(100))) is True
    assert portfolio_value_holder.origin_crypto_currencies_values["USDT"] == decimal.Decimal(constants.ONE / decimal.Decimal(100))
    assert portfolio_value_holder.last_prices_by_trading_pair["BTC/USDT"] == decimal.Decimal(str(100))
