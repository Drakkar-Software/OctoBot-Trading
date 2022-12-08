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
from tests.personal_data.orders.groups import order_mock


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


async def test_on_fill(btps_group):
    order = order_mock()
    # mock btps_group.orders_manager instead of btps_group._balance_orders to allow cythonized class tests
    with mock.patch.object(btps_group.orders_manager, "get_order_from_group", mock.Mock(return_value=[])) \
            as get_order_from_group_mock:
        await btps_group.on_fill(order)
        get_order_from_group_mock.assert_called_once()
        get_order_from_group_mock.reset_mock()

        await btps_group.on_fill(order, ["hi", "ho"])
        get_order_from_group_mock.assert_called_once()
        get_order_from_group_mock.reset_mock()


async def test_on_cancel(btps_group):
    order = order_mock()
    with mock.patch.object(btps_group.orders_manager, "get_order_from_group", mock.Mock(return_value=[])) \
            as get_order_from_group_mock:
        await btps_group.on_cancel(order)
        get_order_from_group_mock.assert_called_once()
        get_order_from_group_mock.reset_mock()

        await btps_group.on_cancel(order, ["hi", "ho"])
        get_order_from_group_mock.assert_called_once()
        get_order_from_group_mock.reset_mock()


async def test_enable(btps_group):
    with mock.patch.object(btps_group.orders_manager, "get_order_from_group", mock.Mock(return_value=[])) \
            as get_order_from_group_mock:
        await btps_group.enable(False)
        get_order_from_group_mock.assert_not_called()
        await btps_group.enable(True)
        get_order_from_group_mock.assert_called_once()
        get_order_from_group_mock.reset_mock()
        await btps_group.enable(True)
        get_order_from_group_mock.assert_called_once()


async def test_can_create_order(btps_group):
    order_1 = order_mock(origin_quantity=decimal.Decimal(1), order_type=enums.TraderOrderType.SELL_LIMIT,
                         origin_price=decimal.Decimal(1), created_last_price=decimal.Decimal(2))
    order_2 = order_mock(origin_quantity=decimal.Decimal(5), order_type=enums.TraderOrderType.BUY_MARKET,
                         origin_price=decimal.Decimal(1), created_last_price=decimal.Decimal(2))
    order_3 = order_mock(origin_quantity=decimal.Decimal(10), order_type=enums.TraderOrderType.TRAILING_STOP,
                         origin_price=decimal.Decimal(1), created_last_price=decimal.Decimal(2))
    with mock.patch.object(btps_group.orders_manager, "get_order_from_group",
                           mock.Mock(return_value=[])) as get_order_from_group_mock:
        # 0 size order
        assert btps_group.can_create_order(enums.TraderOrderType.STOP_LOSS, decimal.Decimal(0)) is True
        get_order_from_group_mock.assert_called_once()
        get_order_from_group_mock.reset_mock()
        # no order, no imbalance
        assert btps_group.can_create_order(enums.TraderOrderType.STOP_LOSS, decimal.Decimal(1)) is False
        get_order_from_group_mock.assert_called_once()
        get_order_from_group_mock.reset_mock()
    with mock.patch.object(btps_group.orders_manager, "get_order_from_group",
                           mock.Mock(return_value=[order_1, order_2, order_3])) as get_order_from_group_mock:
        # enough imbalance
        assert btps_group.can_create_order(enums.TraderOrderType.SELL_LIMIT, decimal.Decimal(1)) is True
        get_order_from_group_mock.assert_called_once()
        get_order_from_group_mock.reset_mock()
        assert btps_group.can_create_order(enums.TraderOrderType.SELL_LIMIT, decimal.Decimal(4)) is True
        get_order_from_group_mock.assert_called_once()
        get_order_from_group_mock.reset_mock()

        # not enough
        assert btps_group.can_create_order(enums.TraderOrderType.SELL_LIMIT, decimal.Decimal("4.000001")) is False
        get_order_from_group_mock.assert_called_once()
        get_order_from_group_mock.reset_mock()
        assert btps_group.can_create_order(enums.TraderOrderType.STOP_LOSS, decimal.Decimal("0.00001")) is False
        get_order_from_group_mock.assert_called_once()
        get_order_from_group_mock.reset_mock()


async def test_get_max_order_quantity(btps_group):
    order_1 = order_mock(origin_quantity=decimal.Decimal(1), order_type=enums.TraderOrderType.SELL_LIMIT,
                         origin_price=decimal.Decimal(1), created_last_price=decimal.Decimal(2))
    order_2 = order_mock(origin_quantity=decimal.Decimal(5), order_type=enums.TraderOrderType.BUY_MARKET,
                         origin_price=decimal.Decimal(1), created_last_price=decimal.Decimal(2))
    order_3 = order_mock(origin_quantity=decimal.Decimal(10), order_type=enums.TraderOrderType.TRAILING_STOP,
                         origin_price=decimal.Decimal(1), created_last_price=decimal.Decimal(2))
    with mock.patch.object(btps_group.orders_manager, "get_order_from_group",
                           mock.Mock(return_value=[])) as get_order_from_group_mock:
        # no order, no imbalance
        assert btps_group.get_max_order_quantity(enums.TraderOrderType.STOP_LOSS) == constants.ZERO
        get_order_from_group_mock.assert_called_once()
        get_order_from_group_mock.reset_mock()
    with mock.patch.object(btps_group.orders_manager, "get_order_from_group",
                           mock.Mock(return_value=[order_1, order_2, order_3])) as get_order_from_group_mock:
        # imbalance
        assert btps_group.get_max_order_quantity(enums.TraderOrderType.SELL_LIMIT) == decimal.Decimal(4)
        get_order_from_group_mock.assert_called_once()
        get_order_from_group_mock.reset_mock()
        assert btps_group.get_max_order_quantity(enums.TraderOrderType.STOP_LOSS) == constants.ZERO
        get_order_from_group_mock.assert_called_once()
        get_order_from_group_mock.reset_mock()


async def test_balance_orders(btps_group):
    order_1 = order_mock(origin_price=decimal.Decimal(1), created_last_price=decimal.Decimal(10),
                         order_type=enums.TraderOrderType.SELL_LIMIT, origin_quantity=decimal.Decimal("1.5"))
    order_2 = order_mock(origin_price=decimal.Decimal(5), created_last_price=decimal.Decimal(3),
                         order_type=enums.TraderOrderType.SELL_LIMIT, origin_quantity=decimal.Decimal("11"))
    order_3 = order_mock(origin_price=decimal.Decimal(10), created_last_price=decimal.Decimal(11),
                         order_type=enums.TraderOrderType.STOP_LOSS, origin_quantity=decimal.Decimal("10"))
    order_4 = order_mock(origin_price=decimal.Decimal(42), created_last_price=decimal.Decimal(2),
                         order_type=enums.TraderOrderType.STOP_LOSS, origin_quantity=decimal.Decimal("20"))
    with mock.patch.object(btps_group.orders_manager, "get_order_from_group",
                           mock.Mock(return_value=[order_1, order_2, order_3, order_4])) as get_order_from_group_mock:
        base_balancing_order = ["existing_order"]
        btps_group.balancing_orders = base_balancing_order
        # 1. not enabled
        btps_group.enabled = False
        await btps_group._balance_orders(order_1, ["ignored_orders"])
        get_order_from_group_mock.assert_not_called()
        assert btps_group.balancing_orders == ["existing_order"]
        assert btps_group.balancing_orders is base_balancing_order

        # 2. enabled
        btps_group.enabled = True
        await btps_group._balance_orders(order_4, ["ignored_orders"])
        get_order_from_group_mock.assert_called_once()
        get_order_from_group_mock.reset_mock()
        order_1.trader.edit_order.assert_not_called()
        order_1.trader.cancel_order.assert_called_once_with(
            order_1, ignored_order=order_4, wait_for_cancelling=True,
            cancelling_timeout=constants.INDIVIDUAL_ORDER_SYNC_TIMEOUT
        )
        order_2.trader.edit_order.assert_called_once_with(
            order_2,
            edited_quantity=decimal.Decimal(10),
            edited_price=None,
            edited_stop_price=None,
            edited_current_price=None,
            params=None
        )
        order_2.trader.cancel_order.assert_not_called()
        order_3.trader.edit_order.assert_not_called()
        order_3.trader.cancel_order.assert_not_called()
        order_4.trader.edit_order.assert_not_called()
        order_4.trader.cancel_order.assert_not_called()
        assert btps_group.balancing_orders == ["existing_order"]
        assert btps_group.balancing_orders is not base_balancing_order  # changed list during orders registration


async def test_get_balance(btps_group):
    order_1 = order_mock(order_type="order_type", origin_price=decimal.Decimal(1),
                         created_last_price=decimal.Decimal(2))
    order_2 = order_mock(order_type="order_type", origin_price=decimal.Decimal(1),
                         created_last_price=decimal.Decimal(2))
    with mock.patch.object(order_util, "is_stop_order", mock.Mock(return_value=False)) as is_stop_order_mock:
        with mock.patch.object(btps_group.orders_manager, "get_order_from_group", mock.Mock(return_value=[])) \
             as get_order_from_group_mock:
            balance = btps_group._get_balance(order_1, None)
            assert balance[btps_group.TAKE_PROFIT].orders == []
            assert balance[btps_group.STOP].orders == []
            get_order_from_group_mock.assert_called_once()
            is_stop_order_mock.assert_not_called()

        with mock.patch.object(btps_group.orders_manager, "get_order_from_group", mock.Mock(return_value=[order_1, order_2])) \
             as get_order_from_group_mock:
            balance = btps_group._get_balance(order_1, None)
            assert balance[btps_group.TAKE_PROFIT].orders == [order_2]
            assert balance[btps_group.STOP].orders == []
            get_order_from_group_mock.assert_called_once()
            is_stop_order_mock.assert_called_once_with("order_type")
            is_stop_order_mock.reset_mock()

        with mock.patch.object(btps_group.orders_manager, "get_order_from_group",
                               mock.Mock(return_value=[order_1, order_2])) as get_order_from_group_mock:
            balance = btps_group._get_balance(order_1, [order_2])
            assert balance[btps_group.TAKE_PROFIT].orders == []
            assert balance[btps_group.STOP].orders == []
            get_order_from_group_mock.assert_called_once()
            is_stop_order_mock.assert_not_called()

    with mock.patch.object(order_util, "is_stop_order", mock.Mock(return_value=True)) as is_stop_order_mock:
        with mock.patch.object(btps_group.orders_manager, "get_order_from_group",
                               mock.Mock(return_value=[order_1, order_2])) as get_order_from_group_mock:
            balance = btps_group._get_balance(order_1, None)
            assert balance[btps_group.TAKE_PROFIT].orders == []
            assert balance[btps_group.STOP].orders == [order_2]
            get_order_from_group_mock.assert_called_once()
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
