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
import mock
import pytest
import decimal

import octobot_trading.constants as constants
import octobot_trading.enums as trading_enums
import octobot_trading.personal_data as trading_personal_data
import octobot_trading.modes.modes_util as modes_util

from tests.exchanges import backtesting_trader, backtesting_config, backtesting_exchange_manager, fake_backtesting
from tests import event_loop

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_get_assets_requiring_extra_price_data_to_convert(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    assert modes_util.get_assets_requiring_extra_price_data_to_convert(exchange_manager, [], "USDT") == set()
    assert modes_util.get_assets_requiring_extra_price_data_to_convert(exchange_manager, ["BTC", "ETH"], "USDT") == {
        "BTC"
    }
    converter = exchange_manager.exchange_personal_data.portfolio_manager.portfolio_value_holder.value_converter
    converter.update_last_price("BTC/USDT", decimal.Decimal(1))
    # no ETH in portfolio
    assert modes_util.get_assets_requiring_extra_price_data_to_convert(exchange_manager, ["BTC", "ETH"], "USDT") \
           == set()
    # same when no backtesting
    exchange_manager.is_backtesting = False
    assert modes_util.get_assets_requiring_extra_price_data_to_convert(exchange_manager, ["BTC", "ETH"], "USDT") \
           == set()
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio.portfolio["ETH"] = \
        trading_personal_data.Asset("ETH", constants.ONE, constants.ONE)
    exchange_manager.exchange_personal_data.portfolio_manager.portfolio.portfolio["SOL"] = \
        trading_personal_data.Asset("SOL", constants.ONE, constants.ONE)
    # ETH in portfolio
    assert sorted(list(modes_util.get_assets_requiring_extra_price_data_to_convert(
        exchange_manager, ["BTC", "ETH", "SOL"], "USDT"
    ))) == sorted(list({'ETH', 'SOL'}))
    converter.update_last_price("BTC/ETH", decimal.Decimal(2))
    # can bridge ETH price using BTC
    assert modes_util.get_assets_requiring_extra_price_data_to_convert(exchange_manager, ["BTC", "ETH"], "USDT") \
           == set()
    exchange_manager.is_backtesting = True
    assert modes_util.get_assets_requiring_extra_price_data_to_convert(exchange_manager, ["BTC", "ETH"], "USDT") \
           == set()


async def test_convert_assets_to_target_asset():
    trading_mode = "trading_mode"
    sellable_assets = ["USDT", "PLOP"]
    target_asset = "USD"
    tickers = {"BTC/USDT": {}}
    with mock.patch.object(
            modes_util, "convert_asset_to_target_asset", mock.AsyncMock(return_value=["orders"])
    ) as convert_asset_to_target_asset:
        orders = \
            await modes_util.convert_assets_to_target_asset(trading_mode, sellable_assets, target_asset, tickers)

        assert convert_asset_to_target_asset.call_count == 2
        assert convert_asset_to_target_asset.mock_calls[0].args == \
               (trading_mode, "USDT", target_asset, {"BTC/USDT": {}})
        assert convert_asset_to_target_asset.mock_calls[0].kwargs == {"asset_amount": None}
        assert convert_asset_to_target_asset.mock_calls[1].args == \
               (trading_mode, "PLOP", target_asset, {"BTC/USDT": {}})
        assert convert_asset_to_target_asset.mock_calls[1].kwargs == {"asset_amount": None}

        assert orders == ["orders", "orders"]

        convert_asset_to_target_asset.reset_mock()
        orders = await modes_util.convert_assets_to_target_asset(trading_mode, [], target_asset, {"tickers": {}})
        convert_asset_to_target_asset.assert_not_called()
        assert orders == []


async def test_convert_asset_to_target_asset(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    trading_mode = _get_trading_mode(exchange_manager)
    sellable_assets = ["USDT", "PLOP"]
    target_asset = "USD"
    tickers = {}
    portfolio = exchange_manager.exchange_personal_data.portfolio_manager.portfolio.portfolio
    converter = exchange_manager.exchange_personal_data.portfolio_manager.portfolio_value_holder.value_converter

    # only BTC and USDT in portfolio
    # convert ETH to USDT: nothing to do
    orders = await modes_util.convert_asset_to_target_asset(trading_mode, "ETH", "USDT", tickers)
    assert orders == []
    trading_mode.create_order.assert_not_called()

    # sell BTC
    orders = await modes_util.convert_asset_to_target_asset(trading_mode, "BTC", "USDT", tickers)
    # not working: no BTC pair in exchange_manager.client_symbols (can't create convert order)
    assert orders == []
    trading_mode.create_order.assert_not_called()

    # add client_symbols pair
    exchange_manager.client_symbols.append("BTC/USDT")

    # not working: no btc price
    assert orders == []
    trading_mode.create_order.assert_not_called()

    # register BTC price
    converter.update_last_price("BTC/USDT", decimal.Decimal(30000))
    orders = await modes_util.convert_asset_to_target_asset(trading_mode, "BTC", "USDT", tickers)
    assert len(orders) == 1
    order = orders[0]
    assert order.order_type == trading_enums.TraderOrderType.SELL_MARKET
    assert order.symbol == "BTC/USDT"
    assert order.origin_quantity == decimal.Decimal(10)
    assert order.created_last_price == decimal.Decimal(30000)
    trading_mode.create_order.assert_called_once()
    trading_mode.create_order.reset_mock()

    orders = await modes_util.convert_asset_to_target_asset(trading_mode, "USDT", "BTC", tickers)
    assert len(orders) == 1
    order = orders[0]
    assert order.order_type == trading_enums.TraderOrderType.BUY_MARKET
    assert order.symbol == "BTC/USDT"
    assert order.origin_quantity == decimal.Decimal("0.03333333")
    assert order.created_last_price == decimal.Decimal(30000)
    trading_mode.create_order.assert_called_once()
    trading_mode.create_order.reset_mock()

    exchange_manager.client_symbols.append("ETH/USDT")
    # using ticker price
    tickers["ETH/USDT"] = {
        trading_enums.ExchangeConstantsTickersColumns.CLOSE.value: decimal.Decimal(1500)
    }

    orders = await modes_util.convert_asset_to_target_asset(trading_mode, "USDT", "ETH", tickers)
    assert len(orders) == 1
    order = orders[0]
    assert order.order_type == trading_enums.TraderOrderType.BUY_MARKET
    assert order.symbol == "ETH/USDT"
    assert order.origin_quantity == decimal.Decimal("0.66666666")
    assert order.created_last_price == decimal.Decimal(1500)
    trading_mode.create_order.assert_called_once()
    trading_mode.create_order.reset_mock()

    orders = await modes_util.convert_asset_to_target_asset(trading_mode, "ETH", "USDT", tickers)
    # no ETH in portfolio
    assert orders == []
    trading_mode.create_order.assert_not_called()

    portfolio["ETH"] = trading_personal_data.Asset("ETH", constants.ONE, constants.ONE)
    orders = await modes_util.convert_asset_to_target_asset(trading_mode, "ETH", "USDT", tickers)
    assert len(orders) == 1
    order = orders[0]
    assert order.order_type == trading_enums.TraderOrderType.SELL_MARKET
    assert order.symbol == "ETH/USDT"
    assert order.origin_quantity == decimal.Decimal("1")
    assert order.created_last_price == decimal.Decimal(1500)
    trading_mode.create_order.assert_called_once()
    trading_mode.create_order.reset_mock()

    # with amount param
    orders = await modes_util.convert_asset_to_target_asset(
        trading_mode, "ETH", "USDT", tickers, asset_amount=decimal.Decimal(2)
    )
    assert len(orders) == 1
    order = orders[0]
    assert order.order_type == trading_enums.TraderOrderType.SELL_MARKET
    assert order.symbol == "ETH/USDT"
    assert order.origin_quantity == decimal.Decimal(2)
    assert order.created_last_price == decimal.Decimal(1500)
    trading_mode.create_order.assert_called_once()
    trading_mode.create_order.reset_mock()

    orders = await modes_util.convert_asset_to_target_asset(
        trading_mode, "USDT", "ETH", tickers, asset_amount=decimal.Decimal(450)
    )
    assert len(orders) == 1
    order = orders[0]
    assert order.order_type == trading_enums.TraderOrderType.BUY_MARKET
    assert order.symbol == "ETH/USDT"
    assert order.origin_quantity == decimal.Decimal("0.3")
    assert order.created_last_price == decimal.Decimal(1500)
    trading_mode.create_order.assert_called_once()
    trading_mode.create_order.reset_mock()


def _get_trading_mode(exchange_manager):
    return mock.Mock(
        exchange_manager=exchange_manager,
        create_order=mock.AsyncMock(side_effect=lambda x: x)
    )
