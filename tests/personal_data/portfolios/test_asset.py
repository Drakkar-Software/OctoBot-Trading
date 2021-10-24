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
import decimal

import octobot_commons.constants as common_constants

import octobot_trading.errors as errors
import octobot_trading.constants as constants
import octobot_trading.personal_data.portfolios.asset as assets

ASSET_CURRENCY_NAME = "BTC"


def test___eq__():
    asset = assets.Asset(ASSET_CURRENCY_NAME, constants.ZERO, constants.ZERO)
    with pytest.raises(NotImplementedError):
        asset == assets.Asset(ASSET_CURRENCY_NAME, constants.ZERO, constants.ZERO)


def test_update():
    asset = assets.Asset(ASSET_CURRENCY_NAME, constants.ZERO, constants.ZERO)
    assert not asset.update(constants.ZERO, constants.ZERO)
    assert asset.update(constants.ZERO, decimal.Decimal(5))
    assert asset.total == decimal.Decimal(5)


def test_set():
    asset = assets.Asset(ASSET_CURRENCY_NAME, constants.ZERO, constants.ZERO)
    assert not asset.set(constants.ZERO, constants.ZERO)
    assert asset.set(decimal.Decimal(5), decimal.Decimal(5))
    assert not asset.set(decimal.Decimal(5), decimal.Decimal(5))
    assert asset.available == decimal.Decimal(5)
    assert asset.total == decimal.Decimal(5)


def test_restore_available():
    asset = assets.Asset(ASSET_CURRENCY_NAME, available=constants.ONE, total=constants.ONE_HUNDRED)
    assert not asset.available == asset.total
    asset.restore_available()
    assert asset.available == asset.total == constants.ONE_HUNDRED


def test_reset():
    asset = assets.Asset(ASSET_CURRENCY_NAME, available=constants.ONE_HUNDRED, total=constants.ONE_HUNDRED)
    assert asset.available == asset.total == constants.ONE_HUNDRED
    asset.reset()
    assert asset.available == asset.total == constants.ZERO


def test_to_dict():
    asset = assets.Asset(ASSET_CURRENCY_NAME, available=constants.ONE_HUNDRED, total=constants.ONE)
    assert asset.to_dict() == {
        common_constants.PORTFOLIO_AVAILABLE: constants.ONE_HUNDRED,
        common_constants.PORTFOLIO_TOTAL: constants.ONE
    }


def test__ensure_update_validity():
    asset = assets.Asset(ASSET_CURRENCY_NAME, available=constants.ONE_HUNDRED, total=decimal.Decimal(2))
    if not os.getenv('CYTHON_IGNORE'):
        with pytest.raises(errors.PortfolioNegativeValueError):
            asset._ensure_update_validity(constants.ONE, decimal.Decimal(-101))
        asset._ensure_update_validity(constants.ZERO, -constants.ZERO)
        with pytest.raises(errors.PortfolioNegativeValueError):
            asset._ensure_update_validity(constants.ZERO, -constants.ONE)
        asset._ensure_update_validity(constants.ONE, -constants.ONE)
        with pytest.raises(errors.PortfolioNegativeValueError):
            asset._ensure_update_validity(-constants.ONE, constants.ZERO)
