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
import pytest

import octobot_trading.personal_data as personal_data
import octobot_trading.personal_data.orders.groups.balanced_take_profit_and_stop_order_group as \
    balanced_take_profit_and_stop_order_group
import octobot_trading.personal_data.orders.groups.trailing_on_filled_tp_balanced_order_group as \
    trailing_on_filled_tp_balanced_order_group
import octobot_trading.personal_data.orders.order_util as order_util
from tests.exchanges import backtesting_config, backtesting_exchange_manager, fake_backtesting


@pytest.fixture
def toftpb_group(backtesting_exchange_manager):
    orders_manager = mock.Mock()
    orders_manager.get_order_from_group = mock.Mock()
    return personal_data.TrailingOnFilledTPBalancedOrderGroup("name",  orders_manager)


@pytest.fixture
def side_balance():
    return balanced_take_profit_and_stop_order_group.SideBalance(None, False)


@pytest.fixture
def trailing_side_balance():
    return trailing_on_filled_tp_balanced_order_group.TrailingSideBalance(None, True)


@pytest.fixture
def order():
    trader = mock.Mock(exchange_manager=mock.Mock())
    target_order = personal_data.Order(trader)
    return target_order


def test_balances_factory(toftpb_group):
    closed_orders = []
    filled = False
    balances = toftpb_group._balances_factory(closed_orders, filled)
    assert isinstance(balances[toftpb_group.TAKE_PROFIT], balanced_take_profit_and_stop_order_group.SideBalance)
    assert isinstance(balances[toftpb_group.STOP], trailing_on_filled_tp_balanced_order_group.TrailingSideBalance)


def test_TrailingSideBalance_get_order_update(trailing_side_balance, order):
    # no trailing profile
    assert trailing_side_balance.get_order_update(order, decimal.Decimal(12)) == {
        personal_data.TrailingOnFilledTPBalancedOrderGroup.ORDER: order,
        personal_data.TrailingOnFilledTPBalancedOrderGroup.UPDATED_QUANTITY: decimal.Decimal(12),
        personal_data.TrailingOnFilledTPBalancedOrderGroup.UPDATED_PRICE: None,
    }

    # incompatible trailing profile
    order.trailing_profile = mock.Mock()
    assert trailing_side_balance.get_order_update(order, decimal.Decimal(12)) == {
        personal_data.TrailingOnFilledTPBalancedOrderGroup.ORDER: order,
        personal_data.TrailingOnFilledTPBalancedOrderGroup.UPDATED_QUANTITY: decimal.Decimal(12),
        personal_data.TrailingOnFilledTPBalancedOrderGroup.UPDATED_PRICE: None,
    }

    order.trailing_profile = personal_data.FilledTakeProfitTrailingProfile([
        personal_data.TrailingPriceStep(price, price, True)
        for price in (10000, 12000, 13000)
    ])
    # filled price does not trigger trailing: trailing trigger price is not reached
    closed_order = personal_data.Order(order.trader)
    closed_order.origin_price = decimal.Decimal(9000)
    trailing_side_balance.closed_order = closed_order
    with mock.patch.object(
        order_util, "get_potentially_outdated_price", mock.Mock(return_value=(decimal.Decimal(8900), True))
    ) as get_potentially_outdated_price_mock:
        assert trailing_side_balance.get_order_update(order, decimal.Decimal(12)) == {
            personal_data.TrailingOnFilledTPBalancedOrderGroup.ORDER: order,
            personal_data.TrailingOnFilledTPBalancedOrderGroup.UPDATED_QUANTITY: decimal.Decimal(12),
            personal_data.TrailingOnFilledTPBalancedOrderGroup.UPDATED_PRICE: None,
        }
        get_potentially_outdated_price_mock.assert_called_once()

    # filled price triggers trailing: trailing trigger price is reached by closed order even though current price is bellow
    closed_order = personal_data.Order(order.trader)
    closed_order.origin_price = decimal.Decimal(10000)
    trailing_side_balance.closed_order = closed_order
    with mock.patch.object(
        order_util, "get_potentially_outdated_price", mock.Mock(return_value=(decimal.Decimal(8900), True))
    ) as get_potentially_outdated_price_mock:
        assert trailing_side_balance.get_order_update(order, decimal.Decimal(12)) == {
            personal_data.TrailingOnFilledTPBalancedOrderGroup.ORDER: order,
            personal_data.TrailingOnFilledTPBalancedOrderGroup.UPDATED_QUANTITY: decimal.Decimal(12),
            personal_data.TrailingOnFilledTPBalancedOrderGroup.UPDATED_PRICE: decimal.Decimal(10000),
        }
        get_potentially_outdated_price_mock.assert_called_once()

    # filled price does not trailing: trailing trigger price is reached by current price even though closed order is bellow
    # BUT trailing threshold has already been reached (trailed already)
    closed_order = personal_data.Order(order.trader)
    closed_order.origin_price = decimal.Decimal(1000)
    trailing_side_balance.closed_order = closed_order
    with mock.patch.object(
        order_util, "get_potentially_outdated_price", mock.Mock(return_value=(decimal.Decimal(10000), True))
    ) as get_potentially_outdated_price_mock:
        assert trailing_side_balance.get_order_update(order, decimal.Decimal(12)) == {
            personal_data.TrailingOnFilledTPBalancedOrderGroup.ORDER: order,
            personal_data.TrailingOnFilledTPBalancedOrderGroup.UPDATED_QUANTITY: decimal.Decimal(12),
            personal_data.TrailingOnFilledTPBalancedOrderGroup.UPDATED_PRICE: None,
        }
        get_potentially_outdated_price_mock.assert_called_once()

    # filled price triggers trailing: trailing trigger price is reached by current price even though closed order is bellow
    closed_order = personal_data.Order(order.trader)
    closed_order.origin_price = decimal.Decimal(1000)
    trailing_side_balance.closed_order = closed_order
    with mock.patch.object(
        order_util, "get_potentially_outdated_price", mock.Mock(return_value=(decimal.Decimal(12000), True))
    ) as get_potentially_outdated_price_mock:
        assert trailing_side_balance.get_order_update(order, decimal.Decimal(12)) == {
            personal_data.TrailingOnFilledTPBalancedOrderGroup.ORDER: order,
            personal_data.TrailingOnFilledTPBalancedOrderGroup.UPDATED_QUANTITY: decimal.Decimal(12),
            personal_data.TrailingOnFilledTPBalancedOrderGroup.UPDATED_PRICE: decimal.Decimal(12000),
        }
        get_potentially_outdated_price_mock.assert_called_once()
