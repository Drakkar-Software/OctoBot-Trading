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
import mock
import os
import pytest

import octobot_commons.asyncio_tools as asyncio_tools
import octobot_commons.symbols as commons_symbols

import octobot_trading.constants as constants
import octobot_trading.errors as errors
import octobot_trading.enums as enums
import octobot_trading.personal_data as personal_data
from tests.test_utils.random_numbers import decimal_random_quantity, decimal_random_price

from tests.exchanges import backtesting_trader, backtesting_config, backtesting_exchange_manager, fake_backtesting
from tests import event_loop

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_get_current_crypto_currencies_values(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder

    assert portfolio_value_holder.get_current_crypto_currencies_values() == \
           {'BTC': constants.ONE, 'USDT': constants.ZERO}
    portfolio_manager.portfolio.update_portfolio_from_balance({
        'BTC': {'available': decimal_random_quantity(), 'total': decimal_random_quantity()},
        'ETH': {'available': decimal_random_quantity(), 'total': decimal_random_quantity()},
        'XRP': {'available': decimal_random_quantity(), 'total': decimal_random_quantity()},
        'DOT': {'available': decimal_random_quantity(), 'total': decimal_random_quantity()},
        'MATIC': {'available': decimal_random_quantity(), 'total': decimal_random_quantity()},
        'USDT': {'available': decimal_random_quantity(), 'total': decimal_random_quantity()}
    }, True)
    portfolio_manager.handle_balance_updated()

    assert portfolio_value_holder.get_current_crypto_currencies_values() == {
        'BTC': constants.ONE,
        'ETH': constants.ZERO,
        'XRP': constants.ZERO,
        'DOT': constants.ZERO,
        'MATIC': constants.ZERO,
        'USDT': constants.ZERO
    }

    exchange_manager.client_symbols.append("MATIC/BTC")
    exchange_manager.client_symbols.append("XRP/BTC")
    if not os.getenv('CYTHON_IGNORE'):
        portfolio_value_holder.value_converter.missing_currency_data_in_exchange.remove("XRP")
        portfolio_manager.handle_mark_price_update("XRP/BTC", decimal.Decimal("0.005"))
        exchange_manager.client_symbols.append("DOT/BTC")
        portfolio_value_holder.value_converter.missing_currency_data_in_exchange.remove("DOT")
        portfolio_manager.handle_mark_price_update("DOT/BTC", decimal.Decimal("0.05"))
        exchange_manager.client_symbols.append("BTC/USDT")

        assert portfolio_value_holder.get_current_crypto_currencies_values() == {
            'BTC': constants.ONE,
            'ETH': constants.ZERO,
            'XRP': decimal.Decimal("0.005"),
            'DOT': decimal.Decimal("0.05"),
            'MATIC': constants.ZERO,
            'USDT': constants.ZERO
        }
        matic_btc_price = decimal_random_price(max_value=decimal.Decimal(0.05))
        portfolio_value_holder.value_converter.missing_currency_data_in_exchange.remove("MATIC")
        portfolio_manager.handle_mark_price_update("MATIC/BTC", matic_btc_price)
        assert portfolio_value_holder.get_current_crypto_currencies_values() == {
            'BTC': constants.ONE,
            'ETH': constants.ZERO,
            'XRP': decimal.Decimal("0.005"),
            'DOT': decimal.Decimal("0.05"),
            'MATIC': matic_btc_price,
            'USDT': constants.ZERO
        }
        usdt_btc_price = decimal_random_price(max_value=decimal.Decimal('0.01'))
        portfolio_value_holder.value_converter.missing_currency_data_in_exchange.remove("USDT")
        portfolio_manager.handle_mark_price_update("BTC/USDT", usdt_btc_price)
        assert portfolio_value_holder.get_current_crypto_currencies_values() == {
            'BTC': constants.ONE,
            'ETH': constants.ZERO,
            'XRP': decimal.Decimal("0.005"),
            'DOT': decimal.Decimal("0.05"),
            'MATIC': matic_btc_price,
            'USDT': constants.ONE / usdt_btc_price
        }
        eth_btc_price = decimal_random_price(max_value=constants.ONE)
        exchange_manager.client_symbols.append("ETH/BTC")
        portfolio_value_holder.value_converter.missing_currency_data_in_exchange.remove("ETH")
        portfolio_manager.handle_mark_price_update("ETH/BTC", eth_btc_price)
        assert portfolio_value_holder.get_current_crypto_currencies_values() == {
            'BTC': constants.ONE,
            'ETH': decimal.Decimal(str(eth_btc_price)),
            'XRP': decimal.Decimal("0.005"),
            'DOT': decimal.Decimal("0.05"),
            'MATIC': matic_btc_price,
            'USDT': constants.ONE / usdt_btc_price
        }


async def test_get_current_holdings_values(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder

    exchange_manager.client_symbols.append("ETH/BTC")
    portfolio_manager.portfolio.update_portfolio_from_balance({
        'BTC': {'available': decimal.Decimal("10"), 'total': decimal.Decimal("10")},
        'ETH': {'available': decimal.Decimal("100"), 'total': decimal.Decimal("100")},
        'XRP': {'available': decimal.Decimal("10000"), 'total': decimal.Decimal("10000")},
        'USDT': {'available': decimal.Decimal("1000"), 'total': decimal.Decimal("1000")}
    }, True)
    portfolio_manager.handle_balance_updated()
    assert portfolio_value_holder.get_current_holdings_values() == {
        'BTC': decimal.Decimal("10"),
        'ETH': constants.ZERO,
        'XRP': constants.ZERO,
        'USDT': constants.ZERO
    }
    portfolio_manager.handle_mark_price_update("ETH/BTC", 50)
    assert portfolio_value_holder.get_current_holdings_values() == {
        'BTC': decimal.Decimal("10"),
        'ETH': decimal.Decimal("5000"),
        'XRP': constants.ZERO,
        'USDT': constants.ZERO
    }
    portfolio_manager.handle_mark_price_update("XRP/USDT", 2.5)
    assert portfolio_value_holder.get_current_holdings_values() == {
        'BTC': decimal.Decimal("10"),
        'ETH': decimal.Decimal("5000"),
        'XRP': constants.ZERO,
        'USDT': constants.ZERO
    }
    portfolio_manager.handle_mark_price_update("XRP/BTC", decimal.Decimal('0.00001'))
    assert portfolio_value_holder.get_current_holdings_values() == {
        'BTC': decimal.Decimal("10"),
        'ETH': decimal.Decimal("5000"),
        'XRP': constants.ZERO,
        'USDT': constants.ZERO
    }
    if not os.getenv('CYTHON_IGNORE'):
        exchange_manager.client_symbols.append("XRP/BTC")
        portfolio_value_holder.value_converter.missing_currency_data_in_exchange.remove("XRP")
        portfolio_manager.handle_mark_price_update("XRP/BTC", decimal.Decimal('0.00001'))
        assert portfolio_value_holder.get_current_holdings_values() == {
            'BTC': decimal.Decimal(10),
            'ETH': decimal.Decimal(5000),
            'XRP': decimal.Decimal(str(0.1)),
            'USDT': constants.ZERO
        }
        exchange_manager.client_symbols.append("BTC/USDT")
        portfolio_value_holder.value_converter.missing_currency_data_in_exchange.remove("USDT")
        portfolio_manager.handle_mark_price_update("BTC/USDT", 5000)
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

    portfolio_manager.handle_profitability_recalculation(True)
    assert portfolio_value_holder.get_origin_portfolio_current_value() == decimal.Decimal(str(10))


async def test_get_origin_portfolio_current_value_with_different_reference_market(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder

    portfolio_manager.reference_market = "USDT"
    portfolio_manager.handle_profitability_recalculation(True)
    assert portfolio_value_holder.get_origin_portfolio_current_value() == decimal.Decimal(str(1000))


async def test_update_origin_crypto_currencies_values(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder

    assert portfolio_value_holder.update_origin_crypto_currencies_values("ETH/BTC", decimal.Decimal(str(0.1))) is True
    assert portfolio_value_holder.origin_crypto_currencies_values["ETH"] == decimal.Decimal(str(0.1))
    assert portfolio_value_holder.value_converter.last_prices_by_trading_pair["ETH/BTC"] == decimal.Decimal(str(0.1))
    # ETH is now priced and BTC is the reference market
    assert portfolio_value_holder.update_origin_crypto_currencies_values("ETH/BTC", decimal.Decimal(str(0.1))) is False

    assert portfolio_value_holder.update_origin_crypto_currencies_values("BTC/USDT", decimal.Decimal(str(100))) is True
    assert portfolio_value_holder.origin_crypto_currencies_values["USDT"] == \
           decimal.Decimal(constants.ONE / decimal.Decimal(100))
    assert portfolio_value_holder.value_converter.last_prices_by_trading_pair["BTC/USDT"] == decimal.Decimal(str(100))
    # USDT is now priced and BTC is the reference market
    assert portfolio_value_holder.update_origin_crypto_currencies_values("BTC/USDT", decimal.Decimal(str(100))) is False

    # with bridge pair (DOT/ETH -> ETH/BTC to compute DOT/BTC)
    assert portfolio_value_holder.update_origin_crypto_currencies_values("DOT/ETH", decimal.Decimal(str(0.015))) is True
    assert portfolio_value_holder.origin_crypto_currencies_values["DOT"] == \
           decimal.Decimal(str(0.015)) * decimal.Decimal(str(0.1))
    assert portfolio_value_holder.value_converter.last_prices_by_trading_pair["DOT/ETH"] == decimal.Decimal(str(0.015))
    # USDT is now priced and BTC is the reference market
    assert portfolio_value_holder.update_origin_crypto_currencies_values("DOT/ETH", decimal.Decimal(str(0.015))) \
           is False


async def test_get_holdings_ratio(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder
    symbol = "BTC/USDT"
    exchange_manager.client_symbols = [symbol]
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio_value_holder.\
        value_converter.last_prices_by_trading_pair[symbol] = decimal.Decimal("1000")
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio_value_holder.\
        portfolio_current_value = decimal.Decimal("11")
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio.portfolio = {}
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio.portfolio["BTC"] = \
        personal_data.SpotAsset(name="BTC", available=decimal.Decimal("10"), total=decimal.Decimal("10"))
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio.portfolio["USDT"] = \
        personal_data.SpotAsset(name="USDT", available=decimal.Decimal("1000"), total=decimal.Decimal("1000"))

    assert portfolio_value_holder.get_holdings_ratio("BTC") == decimal.Decimal('0.9090909090909090909090909091')
    assert portfolio_value_holder.get_holdings_ratio("BTC", include_assets_in_open_orders=False) \
           == decimal.Decimal('0.9090909090909090909090909091')
    assert portfolio_value_holder.get_holdings_ratio("USDT") == decimal.Decimal('0.09090909090909090909090909091')

    exchange_manager.exchange_personal_data.portfolio_manager.portfolio.portfolio.pop("USDT")
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio_value_holder.\
        portfolio_current_value = decimal.Decimal("10")
    assert portfolio_value_holder.get_holdings_ratio("BTC") == constants.ONE
    # add ETH and try to get ratio without symbol price
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio.\
        get_currency_portfolio("ETH").total = decimal.Decimal(10)
    # force not backtesting mode
    exchange_manager.is_backtesting = False
    # force add symbol in exchange symbols
    exchange_manager.client_symbols.append("ETH/BTC")
    with pytest.raises(errors.MissingPriceDataError):
        ratio = portfolio_value_holder.get_holdings_ratio("ETH")
    # let channel register proceed
    await asyncio_tools.wait_asyncio_next_cycle()
    assert portfolio_value_holder.get_holdings_ratio("BTC") == constants.ONE
    assert portfolio_value_holder.get_holdings_ratio("USDT") == constants.ZERO
    assert portfolio_value_holder.get_holdings_ratio("XYZ") == constants.ZERO

    # without traded_symbols
    assert portfolio_value_holder.get_holdings_ratio("BTC", traded_symbols_only=True) == constants.ZERO

    # with traded_symbols
    exchange_manager.exchange_config.traded_symbols.extend([
        commons_symbols.parse_symbol("BTC/USDT"), commons_symbols.parse_symbol("ETH/USDT")
    ])
    assert portfolio_value_holder.get_holdings_ratio("BTC", traded_symbols_only=True) == constants.ONE

async def test_get_holdings_ratio_with_include_assets_in_open_orders(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder
    symbol = "BTC/USDT"
    exchange_manager.client_symbols = [symbol]
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio_value_holder.\
        value_converter.last_prices_by_trading_pair[symbol] = decimal.Decimal("1000")
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio_value_holder.\
        value_converter.last_prices_by_trading_pair["ETH/USDT"] = decimal.Decimal("100")
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio_value_holder.\
        portfolio_current_value = decimal.Decimal("11")
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio.portfolio = {}
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio.portfolio["BTC"] = \
        personal_data.SpotAsset(name="BTC", available=decimal.Decimal("10"), total=decimal.Decimal("10"))
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio.portfolio["USDT"] = \
        personal_data.SpotAsset(name="USDT", available=decimal.Decimal("1000"), total=decimal.Decimal("1000"))

    assert portfolio_value_holder.get_holdings_ratio("BTC", include_assets_in_open_orders=False) \
           == decimal.Decimal('0.9090909090909090909090909091')
    assert portfolio_value_holder.get_holdings_ratio("USDT", include_assets_in_open_orders=False) \
           == decimal.Decimal('0.09090909090909090909090909091')

    # no open order
    assert portfolio_value_holder.get_holdings_ratio("BTC", include_assets_in_open_orders=True) \
           == decimal.Decimal('0.9090909090909090909090909091')
    assert portfolio_value_holder.get_holdings_ratio("USDT", include_assets_in_open_orders=True) \
           == decimal.Decimal('0.09090909090909090909090909091')

    order_1 = mock.Mock(
        order_id="1", symbol="BTC/USDT", origin_quantity=decimal.Decimal("1"), total_cost=decimal.Decimal('1000'),
        status=enums.OrderStatus.OPEN, side=enums.TradeOrderSide.BUY
    )
    order_2 = mock.Mock(
        order_id="2", symbol="ETH/USDT", origin_quantity=decimal.Decimal("2"), total_cost=decimal.Decimal('100'),
        status=enums.OrderStatus.OPEN, side=enums.TradeOrderSide.BUY
    )
    order_3 = mock.Mock(
        order_id="3", symbol="XRP/ETH", origin_quantity=decimal.Decimal("100"), total_cost=decimal.Decimal('0.001'),
        status=enums.OrderStatus.OPEN, side=enums.TradeOrderSide.SELL
    )
    # open orders
    await exchange_manager.exchange_personal_data.orders_manager.upsert_order_instance(order_1)
    await exchange_manager.exchange_personal_data.orders_manager.upsert_order_instance(order_2)
    assert portfolio_value_holder.get_holdings_ratio("BTC", include_assets_in_open_orders=False) \
           == decimal.Decimal('0.9090909090909090909090909091')
    assert portfolio_value_holder.get_holdings_ratio("ETH", include_assets_in_open_orders=False) \
           == decimal.Decimal('0')
    assert portfolio_value_holder.get_holdings_ratio("USDT", include_assets_in_open_orders=False) \
           == decimal.Decimal('0.09090909090909090909090909091')

    assert portfolio_value_holder.get_holdings_ratio("BTC", include_assets_in_open_orders=True) \
           == decimal.Decimal('1')
    assert portfolio_value_holder.get_holdings_ratio("ETH", include_assets_in_open_orders=True) \
           == decimal.Decimal('0.01818181818181818181818181818')
    assert portfolio_value_holder.get_holdings_ratio("USDT", include_assets_in_open_orders=True) \
           == decimal.Decimal('0.09090909090909090909090909091')

    await exchange_manager.exchange_personal_data.orders_manager.upsert_order_instance(order_3)
    assert portfolio_value_holder.get_holdings_ratio("BTC", include_assets_in_open_orders=True) \
           == decimal.Decimal('1')
    assert portfolio_value_holder.get_holdings_ratio("ETH", include_assets_in_open_orders=True) \
           == decimal.Decimal('0.01819090909090909090909090909')
    assert portfolio_value_holder.get_holdings_ratio("USDT", include_assets_in_open_orders=True) \
           == decimal.Decimal('0.09090909090909090909090909091')

    # without traded_symbols
    assert portfolio_value_holder.get_holdings_ratio(
        "BTC", traded_symbols_only=True, include_assets_in_open_orders=True
    ) == constants.ZERO

    # with traded_symbols
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio.portfolio["ETH"] = \
        personal_data.SpotAsset(name="ETH", available=decimal.Decimal("10"), total=decimal.Decimal("10"))
    exchange_manager.exchange_config.traded_symbols.extend([
        commons_symbols.parse_symbol("BTC/USDT")
    ])
    assert portfolio_value_holder.get_holdings_ratio(
        "BTC", traded_symbols_only=True, include_assets_in_open_orders=True
    ) == constants.ONE
    assert portfolio_value_holder.get_holdings_ratio(
        "ETH", traded_symbols_only=True, include_assets_in_open_orders=True
    ) == decimal.Decimal('0.1091')

    # ETH now in traded assets
    exchange_manager.exchange_config.traded_symbols.extend([
        commons_symbols.parse_symbol("ETH/USDT")
    ])
    assert portfolio_value_holder.get_holdings_ratio(
        "ETH", traded_symbols_only=True, include_assets_in_open_orders=True
    ) == decimal.Decimal('0.1000083333333333333333333333')  # ETH now taken into account in total value
    # ETH now taken into account in total value: BTC % of holdings is not 1 anymore (as ETH takes a part of this %)
    assert portfolio_value_holder.get_holdings_ratio(
        "BTC", traded_symbols_only=True, include_assets_in_open_orders=True
    ) == decimal.Decimal('0.9166666666666666666666666667')
