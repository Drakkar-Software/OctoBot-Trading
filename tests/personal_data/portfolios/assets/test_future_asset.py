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

import octobot_trading.constants as constants
import octobot_trading.personal_data.portfolios.assets.future_asset as future_asset

ASSET_CURRENCY_NAME = "BTC"


def test___eq__():
    asset = future_asset.FutureAsset(ASSET_CURRENCY_NAME, constants.ZERO, constants.ZERO)
    assert asset == future_asset.FutureAsset(ASSET_CURRENCY_NAME, constants.ZERO, constants.ZERO)
    assert not asset == future_asset.FutureAsset(ASSET_CURRENCY_NAME, constants.ONE_HUNDRED, constants.ZERO)
    assert not asset == future_asset.FutureAsset(ASSET_CURRENCY_NAME, constants.ZERO, constants.ONE_HUNDRED)
    assert not asset == future_asset.FutureAsset(ASSET_CURRENCY_NAME, constants.ZERO, constants.ZERO,
                                                 wallet_balance=constants.ONE_HUNDRED)
    assert asset == future_asset.FutureAsset(ASSET_CURRENCY_NAME, constants.ZERO, constants.ZERO,
                                             wallet_balance=constants.ZERO)
    assert not asset == future_asset.FutureAsset(ASSET_CURRENCY_NAME, constants.ZERO, constants.ZERO,
                                                 position_margin=constants.ONE_HUNDRED)
    assert not asset == future_asset.FutureAsset(ASSET_CURRENCY_NAME, constants.ZERO, constants.ZERO,
                                                 maintenance_margin=constants.ONE_HUNDRED)
    assert not asset == future_asset.FutureAsset(ASSET_CURRENCY_NAME, constants.ZERO, constants.ZERO,
                                                 initial_margin=constants.ONE_HUNDRED)


def test_update():
    asset = future_asset.FutureAsset(ASSET_CURRENCY_NAME,
                                     available=constants.ZERO, total=constants.ZERO, order_margin=constants.ZERO,
                                     initial_margin=constants.ZERO, wallet_balance=constants.ZERO,
                                     maintenance_margin=constants.ZERO, position_margin=constants.ZERO)
    assert not asset.update(available=constants.ZERO, total=constants.ZERO, wallet_balance=constants.ZERO)
    assert asset.total == constants.ZERO
    assert asset.update(available=constants.ZERO, total=decimal.Decimal(5), wallet_balance=constants.ZERO)
    assert asset.total == decimal.Decimal(5)
    assert asset.update(available=constants.ZERO, total=decimal.Decimal(6), wallet_balance=decimal.Decimal(10))
    assert asset.total == decimal.Decimal(11)
    assert asset.wallet_balance == decimal.Decimal(10)
    assert asset.update(available=constants.ZERO, total=constants.ZERO, wallet_balance=decimal.Decimal(10),
                        maintenance_margin=decimal.Decimal(3))
    assert asset.wallet_balance == decimal.Decimal(20)
    assert asset.total == decimal.Decimal(31)
    assert asset.maintenance_margin == decimal.Decimal(3)
    assert asset.available == constants.ZERO


def test_set():
    asset = future_asset.FutureAsset(ASSET_CURRENCY_NAME,
                                     available=constants.ZERO, total=constants.ZERO, order_margin=constants.ZERO,
                                     initial_margin=constants.ZERO, wallet_balance=constants.ZERO,
                                     maintenance_margin=constants.ZERO, position_margin=constants.ZERO)
    assert not asset.set(available=constants.ZERO, total=constants.ZERO, wallet_balance=constants.ZERO)
    assert asset.set(available=decimal.Decimal(5), total=decimal.Decimal(5), wallet_balance=decimal.Decimal(2))
    assert not asset.set(available=decimal.Decimal(5), total=decimal.Decimal(5), wallet_balance=decimal.Decimal(2))
    assert asset.available == decimal.Decimal(5)
    assert asset.total == decimal.Decimal(5)
    assert asset.wallet_balance == decimal.Decimal(2)


def test_restore_available():
    asset = future_asset.FutureAsset(ASSET_CURRENCY_NAME, available=constants.ONE, total=constants.ONE_HUNDRED)
    assert not asset.available == asset.total
    asset.restore_available()
    assert asset.available == asset.total == constants.ONE_HUNDRED


def test_reset():
    asset = future_asset.FutureAsset(ASSET_CURRENCY_NAME,
                                     available=constants.ONE_HUNDRED, total=constants.ONE_HUNDRED,
                                     initial_margin=constants.ONE_HUNDRED, wallet_balance=constants.ONE_HUNDRED,
                                     maintenance_margin=constants.ONE_HUNDRED, order_margin=constants.ONE_HUNDRED,
                                     position_margin=constants.ONE_HUNDRED)
    assert asset.available == asset.total == asset.initial_margin == asset.wallet_balance == \
           asset.maintenance_margin == asset.position_margin == asset.order_margin == constants.ONE_HUNDRED
    asset.reset()
    assert asset.available == asset.total == asset.initial_margin == asset.wallet_balance == \
           asset.maintenance_margin == asset.position_margin == asset.order_margin == constants.ZERO
