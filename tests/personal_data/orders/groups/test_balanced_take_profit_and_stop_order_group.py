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
import octobot_trading.constants as constants
import octobot_trading.enums as enums
import octobot_trading.personal_data.orders.order_util as order_util
from tests.exchanges import backtesting_config, backtesting_exchange_manager, fake_backtesting


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


@pytest.fixture
def btps_group(backtesting_exchange_manager):
    orders_manager = mock.Mock()
    orders_manager.get_order_from_group = mock.Mock()
    return personal_data.BalancedTakeProfitAndStopOrderGroup("name",  orders_manager)


@pytest.fixture
def side_balance():
    return balanced_take_profit_and_stop_order_group._SideBalance()


def order_mock(**kwargs):
    order = mock.Mock(**kwargs)
    order.is_open = mock.Mock(return_value=True)
    order.trader = mock.Mock()
    order.trader.cancel_order = mock.AsyncMock()
    order.trader.edit_order = mock.AsyncMock()
    return order


async def test_on_fill(btps_group):
    order = order_mock()
    with mock.patch.object(btps_group, "_balance_orders", mock.AsyncMock()) as _balance_orders_mock:
        await btps_group.on_fill(order)
        _balance_orders_mock.assert_called_once_with(order, None)
        _balance_orders_mock.reset_mock()

        await btps_group.on_fill(order, ["hi", "ho"])
        _balance_orders_mock.assert_called_once_with(order, ["hi", "ho"])
        _balance_orders_mock.reset_mock()


async def test_on_cancel(btps_group):
    order = order_mock()
    with mock.patch.object(btps_group, "_balance_orders", mock.AsyncMock()) as _balance_orders_mock:
        await btps_group.on_cancel(order)
        _balance_orders_mock.assert_called_once_with(order, None)
        _balance_orders_mock.reset_mock()

        await btps_group.on_cancel(order, ["hi", "ho"])
        _balance_orders_mock.assert_called_once_with(order, ["hi", "ho"])
        _balance_orders_mock.reset_mock()


async def test_enable(btps_group):
    with mock.patch.object(btps_group, "_balance_orders", mock.AsyncMock()) as _balance_orders_mock:
        await btps_group.enable(False)
        _balance_orders_mock.assert_not_called()
        await btps_group.enable(True)
        _balance_orders_mock.assert_called_once_with(None, None)
        _balance_orders_mock.reset_mock()
        await btps_group.enable(True)
        _balance_orders_mock.assert_called_once_with(None, None)


async def test_can_create_order(btps_group):
    order_1 = order_mock(origin_quantity=decimal.Decimal(1))
    order_2 = order_mock(origin_quantity=decimal.Decimal(5))
    order_3 = order_mock(origin_quantity=decimal.Decimal(10))
    balance_take_profit = balanced_take_profit_and_stop_order_group._SideBalance()
    balance_stop = balanced_take_profit_and_stop_order_group._SideBalance()
    with mock.patch.object(btps_group, "_get_balance", mock.Mock(return_value={
            btps_group.TAKE_PROFIT: balance_take_profit,
            btps_group.STOP: balance_stop
        })) as _balance_orders_mock:
        # 0 size order
        assert btps_group.can_create_order(enums.TraderOrderType.STOP_LOSS, decimal.Decimal(0)) is True
        _balance_orders_mock.assert_called_once_with(None, None)
        # no order, no imbalance
        assert btps_group.can_create_order(enums.TraderOrderType.STOP_LOSS, decimal.Decimal(1)) is False
        balance_take_profit.orders = [order_1, order_2]
        balance_stop.orders = [order_3]
        # enough imbalance
        assert btps_group.can_create_order(enums.TraderOrderType.SELL_LIMIT, decimal.Decimal(1)) is True
        assert btps_group.can_create_order(enums.TraderOrderType.SELL_LIMIT, decimal.Decimal(4)) is True

        # not enough
        assert btps_group.can_create_order(enums.TraderOrderType.SELL_LIMIT, decimal.Decimal("4.000001")) is False
        assert btps_group.can_create_order(enums.TraderOrderType.STOP_LOSS, decimal.Decimal("0.00001")) is False


async def test_balance_orders(btps_group):
    order_1 = order_mock(origin_price=decimal.Decimal(1), created_last_price=decimal.Decimal(2))
    order_2 = order_mock(origin_price=decimal.Decimal(5), created_last_price=decimal.Decimal(3))
    order_3 = order_mock(origin_price=decimal.Decimal(10), created_last_price=decimal.Decimal(11))
    balance_take_profit = balanced_take_profit_and_stop_order_group._SideBalance()
    balance_take_profit.add_order(order_1)
    balance_take_profit.add_order(order_2)
    balance_stop = balanced_take_profit_and_stop_order_group._SideBalance()
    balance_stop.add_order(order_3)
    with mock.patch.object(btps_group, "_get_balance", mock.Mock(return_value={
            btps_group.TAKE_PROFIT: balance_take_profit,
            btps_group.STOP: balance_stop
        })) as _balance_orders_mock, \
        mock.patch.object(balance_take_profit, "get_actions_to_balance",
                          mock.Mock(return_value={
                              btps_group.UPDATE: [
                                  {
                                      btps_group.UPDATED_QUANTITY: decimal.Decimal(1),
                                      btps_group.ORDER: order_1,
                                  }
                              ],
                              btps_group.CANCEL: [order_3]
                          })) as balance_take_profit_get_actions_to_balance_mock, \
        mock.patch.object(balance_stop, "get_actions_to_balance",
                          mock.Mock(return_value={
                              btps_group.UPDATE: [
                                  {
                                      btps_group.UPDATED_QUANTITY: decimal.Decimal(3),
                                      btps_group.ORDER: order_2,
                                  }
                              ],
                              btps_group.CANCEL: []
                          })) as balance_stop_get_actions_to_balance_mock, \
        mock.patch.object(balanced_take_profit_and_stop_order_group._SideBalance, "get_balance",
                          mock.Mock(return_value=constants.ZERO)) as get_balance_mock:
        base_balancing_order = ["existing_order"]
        btps_group.balancing_orders = base_balancing_order
        # 1. not enabled
        btps_group.enabled = False
        await btps_group._balance_orders(order_1, ["ignored_orders"])
        _balance_orders_mock.assert_not_called()
        balance_take_profit_get_actions_to_balance_mock.assert_not_called()
        balance_stop_get_actions_to_balance_mock.assert_not_called()
        get_balance_mock.assert_not_called()
        assert btps_group.balancing_orders == ["existing_order"]
        assert btps_group.balancing_orders is base_balancing_order

        # 2. enabled
        btps_group.enabled = True
        await btps_group._balance_orders(order_1, ["ignored_orders"])
        _balance_orders_mock.assert_called_once_with(order_1, ["ignored_orders"])
        balance_take_profit_get_actions_to_balance_mock.assert_called_once_with(constants.ZERO)
        balance_stop_get_actions_to_balance_mock.assert_called_once_with(constants.ZERO)
        assert get_balance_mock.call_count == 2
        order_1.trader.edit_order.assert_called_once_with(order_1, edited_quantity=decimal.Decimal(1))
        order_1.trader.cancel_order.assert_not_called()
        order_2.trader.edit_order.assert_called_once_with(order_2, edited_quantity=decimal.Decimal(3))
        order_2.trader.cancel_order.assert_not_called()
        order_3.trader.edit_order.assert_not_called()
        order_3.trader.cancel_order.assert_called_once_with(order_3, ignored_order=order_1)
        assert btps_group.balancing_orders == ["existing_order"]
        assert btps_group.balancing_orders is not base_balancing_order  # changed list during orders registration


async def test_get_balance(btps_group):
    order_1 = order_mock(order_type="order_type", origin_price=decimal.Decimal(1),
                         created_last_price=decimal.Decimal(2))
    order_2 = order_mock(order_type="order_type", origin_price=decimal.Decimal(1),
                         created_last_price=decimal.Decimal(2))
    with mock.patch.object(order_util, "is_stop_order", mock.Mock(return_value=False)) as is_stop_order_mock:
        with mock.patch.object(btps_group, "get_group_open_orders", mock.Mock(return_value=[])) \
             as get_group_open_orders_mock:
            balance = btps_group._get_balance(order_1, None)
            assert balance[btps_group.TAKE_PROFIT].orders == []
            assert balance[btps_group.STOP].orders == []
            get_group_open_orders_mock.assert_called_once()
            is_stop_order_mock.assert_not_called()

        with mock.patch.object(btps_group, "get_group_open_orders", mock.Mock(return_value=[order_1, order_2])) \
             as get_group_open_orders_mock:
            balance = btps_group._get_balance(order_1, None)
            assert balance[btps_group.TAKE_PROFIT].orders == [order_2]
            assert balance[btps_group.STOP].orders == []
            get_group_open_orders_mock.assert_called_once()
            is_stop_order_mock.assert_called_once_with("order_type")
            is_stop_order_mock.reset_mock()

        with mock.patch.object(btps_group, "get_group_open_orders", mock.Mock(return_value=[order_1, order_2])) \
             as get_group_open_orders_mock:
            balance = btps_group._get_balance(order_1, [order_2])
            assert balance[btps_group.TAKE_PROFIT].orders == []
            assert balance[btps_group.STOP].orders == []
            get_group_open_orders_mock.assert_called_once()
            is_stop_order_mock.assert_not_called()

    with mock.patch.object(order_util, "is_stop_order", mock.Mock(return_value=True)) as is_stop_order_mock:
        with mock.patch.object(btps_group, "get_group_open_orders", mock.Mock(return_value=[order_1, order_2])) \
             as get_group_open_orders_mock:
            balance = btps_group._get_balance(order_1, None)
            assert balance[btps_group.TAKE_PROFIT].orders == []
            assert balance[btps_group.STOP].orders == [order_2]
            get_group_open_orders_mock.assert_called_once()
            is_stop_order_mock.assert_called_once_with("order_type")
            is_stop_order_mock.reset_mock()


async def test_SideBalance_add_order(side_balance):
    assert side_balance.orders == []
    order_1 = order_mock(origin_price=decimal.Decimal(1), created_last_price=decimal.Decimal(2))
    order_2 = order_mock(origin_price=decimal.Decimal(15), created_last_price=decimal.Decimal(3))
    order_3 = order_mock(origin_price=decimal.Decimal(50), created_last_price=decimal.Decimal(55))
    side_balance.add_order(order_1)
    assert side_balance.orders == [order_1]
    side_balance.add_order(order_2)
    assert side_balance.orders == [order_2, order_1]
    side_balance.add_order(order_3)
    assert side_balance.orders == [order_2, order_3, order_1]


async def test_SideBalance_get_actions_to_balance_special_inputs(side_balance):
    with mock.patch.object(side_balance, "get_balance", mock.Mock(return_value=decimal.Decimal("-1"))):
        # target balance can't be negative (order quantity is always positive). value treated as abs()
        assert side_balance.get_actions_to_balance(constants.ONE) == {
            personal_data.BalancedTakeProfitAndStopOrderGroup.CANCEL: [],
            personal_data.BalancedTakeProfitAndStopOrderGroup.UPDATE: [],
        }
    with mock.patch.object(side_balance, "get_balance", mock.Mock(return_value=constants.ONE)):
        # target balance == balance: nothing to do
        assert side_balance.get_actions_to_balance(constants.ONE) == {
            personal_data.BalancedTakeProfitAndStopOrderGroup.CANCEL: [],
            personal_data.BalancedTakeProfitAndStopOrderGroup.UPDATE: [],
        }
    with mock.patch.object(side_balance, "get_balance", mock.Mock(return_value=constants.ONE)):
        # target balance > balance: nothing to do (can't create order to increase)
        assert side_balance.get_actions_to_balance(decimal.Decimal("0.6")) == {
            personal_data.BalancedTakeProfitAndStopOrderGroup.CANCEL: [],
            personal_data.BalancedTakeProfitAndStopOrderGroup.UPDATE: [],
        }
    with mock.patch.object(side_balance, "get_balance", mock.Mock(return_value=constants.ONE)):
        # no order to create actions
        assert side_balance.get_actions_to_balance(decimal.Decimal("10")) == {
            personal_data.BalancedTakeProfitAndStopOrderGroup.CANCEL: [],
            personal_data.BalancedTakeProfitAndStopOrderGroup.UPDATE: [],
        }


async def test_SideBalance_get_actions_to_balance_normal_inputs(side_balance):
    order_0_1 = order_mock(origin_quantity=decimal.Decimal("2.899999"))
    order_0_2 = order_mock(origin_quantity=decimal.Decimal("0.111111"))
    order_0_3 = order_mock(origin_quantity=decimal.Decimal("3.15545145441"))
    side_balance.orders = [order_0_1, order_0_2, order_0_3]
    assert side_balance.get_actions_to_balance(decimal.Decimal("3.15545145441")) == {
        personal_data.BalancedTakeProfitAndStopOrderGroup.CANCEL: [order_0_1, order_0_2],
        personal_data.BalancedTakeProfitAndStopOrderGroup.UPDATE: [],
    }
    order_1 = order_mock(origin_quantity=decimal.Decimal("1"))
    order_2 = order_mock(origin_quantity=decimal.Decimal("6.42"))
    side_balance.orders = [order_2]
    assert side_balance.get_actions_to_balance(decimal.Decimal("3")) == {
        personal_data.BalancedTakeProfitAndStopOrderGroup.CANCEL: [],
        personal_data.BalancedTakeProfitAndStopOrderGroup.UPDATE: [{
            personal_data.BalancedTakeProfitAndStopOrderGroup.ORDER: order_2,
            personal_data.BalancedTakeProfitAndStopOrderGroup.UPDATED_QUANTITY: decimal.Decimal("3"),
        }],
    }
    side_balance.orders = [order_1, order_2]
    assert side_balance.get_actions_to_balance(decimal.Decimal("3")) == {
        personal_data.BalancedTakeProfitAndStopOrderGroup.CANCEL: [order_1],
        personal_data.BalancedTakeProfitAndStopOrderGroup.UPDATE: [{
            personal_data.BalancedTakeProfitAndStopOrderGroup.ORDER: order_2,
            personal_data.BalancedTakeProfitAndStopOrderGroup.UPDATED_QUANTITY: decimal.Decimal("3"),
        }],
    }
    order_2 = order_mock(origin_quantity=decimal.Decimal("6.42"))
    order_3 = order_mock(origin_quantity=decimal.Decimal("11.888998327557457"))
    side_balance.orders = [order_1, order_2, order_3]
    assert side_balance.get_actions_to_balance(decimal.Decimal("3")) == {
        personal_data.BalancedTakeProfitAndStopOrderGroup.CANCEL: [order_1, order_2],
        personal_data.BalancedTakeProfitAndStopOrderGroup.UPDATE: [{
            personal_data.BalancedTakeProfitAndStopOrderGroup.ORDER: order_3,
            personal_data.BalancedTakeProfitAndStopOrderGroup.UPDATED_QUANTITY: decimal.Decimal("3"),
        }],
    }
    order_4 = order_mock(origin_quantity=decimal.Decimal("0.1"))
    side_balance.orders = [order_1, order_2, order_3, order_4]
    # keep order_4 untouched as it is the closest from price and can be included in target balance
    assert side_balance.get_actions_to_balance(decimal.Decimal("3")) == {
        personal_data.BalancedTakeProfitAndStopOrderGroup.CANCEL: [order_1, order_2],
        personal_data.BalancedTakeProfitAndStopOrderGroup.UPDATE: [{
            personal_data.BalancedTakeProfitAndStopOrderGroup.ORDER: order_3,
            personal_data.BalancedTakeProfitAndStopOrderGroup.UPDATED_QUANTITY: decimal.Decimal("2.9"),
        }],
    }
    side_balance.orders = [order_1, order_4, order_2, order_3]
    assert side_balance.get_actions_to_balance(decimal.Decimal("3")) == {
        personal_data.BalancedTakeProfitAndStopOrderGroup.CANCEL: [order_1, order_4, order_2],
        personal_data.BalancedTakeProfitAndStopOrderGroup.UPDATE: [{
            personal_data.BalancedTakeProfitAndStopOrderGroup.ORDER: order_3,
            personal_data.BalancedTakeProfitAndStopOrderGroup.UPDATED_QUANTITY: decimal.Decimal("3"),
        }],
    }

    side_balance.orders = [order_1, order_4, order_2, order_3]
    assert side_balance.get_actions_to_balance(constants.ZERO) == {
        personal_data.BalancedTakeProfitAndStopOrderGroup.CANCEL: [order_1, order_4, order_2, order_3],
        personal_data.BalancedTakeProfitAndStopOrderGroup.UPDATE: [],
    }


async def test_SideBalance_get_balance(side_balance):
    assert side_balance.get_balance() is constants.ZERO
    order_1 = order_mock(origin_quantity=decimal.Decimal(1))
    order_2 = order_mock(origin_quantity=decimal.Decimal(10))
    order_mock(origin_quantity=decimal.Decimal(50))
    side_balance.orders = [order_1, order_2]
    assert side_balance.get_balance() == decimal.Decimal(11)
