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

import octobot_trading.personal_data as personal_data
import octobot_trading.errors as errors
from tests.exchanges import backtesting_config, backtesting_exchange_manager, fake_backtesting


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


@pytest.fixture
def oco_group(backtesting_exchange_manager):
    orders_manager = mock.Mock()
    orders_manager.get_order_from_group = mock.Mock()
    return personal_data.OneCancelsTheOtherOrderGroup("name",  orders_manager)


def order_mock():
    order = mock.Mock()
    order.is_open = mock.Mock(return_value=True)
    order.trader = mock.Mock()
    order.trader.cancel_order = mock.AsyncMock()
    return order


async def test_on_fill(oco_group):
    order = order_mock()
    with mock.patch.object(oco_group.orders_manager, "get_order_from_group", mock.Mock(return_value=[])) \
         as get_order_from_group_mock:
        await oco_group.on_fill(order)
        order.trader.cancel_order.assert_not_called()
        get_order_from_group_mock.assert_called_once_with(oco_group.name)
    with mock.patch.object(oco_group.orders_manager, "get_order_from_group", mock.Mock(return_value=[order])) \
         as get_order_from_group_mock:
        await oco_group.on_fill(order, ignored_orders=["hello"])
        order.trader.cancel_order.assert_not_called()
        get_order_from_group_mock.assert_called_once_with(oco_group.name)
    other_order = order_mock()
    with mock.patch.object(oco_group.orders_manager, "get_order_from_group", mock.Mock(return_value=[order,
                                                                                                     other_order])) \
         as get_order_from_group_mock:
        await oco_group.on_fill(order)
        order.trader.cancel_order.assert_not_called()
        other_order.trader.cancel_order.assert_called_once_with(other_order, ignored_order=order)
        get_order_from_group_mock.assert_called_once_with(oco_group.name)


async def test_on_cancel(oco_group):
    order = order_mock()
    with mock.patch.object(oco_group.orders_manager, "get_order_from_group", mock.Mock(return_value=[])) \
         as get_order_from_group_mock:
        await oco_group.on_cancel(order)
        order.trader.cancel_order.assert_not_called()
        get_order_from_group_mock.assert_called_once_with(oco_group.name)
    with mock.patch.object(oco_group.orders_manager, "get_order_from_group", mock.Mock(return_value=[order])) \
         as get_order_from_group_mock:
        await oco_group.on_cancel(order, ignored_orders=["hi"])
        order.trader.cancel_order.assert_not_called()
        get_order_from_group_mock.assert_called_once_with(oco_group.name)
        get_order_from_group_mock.reset_mock()
        with pytest.raises(errors.OrderGroupTriggerArgumentError):
            await oco_group.on_cancel(order, ignored_orders=["hi", "ho"])
        order.trader.cancel_order.assert_not_called()
        get_order_from_group_mock.assert_not_called()
    other_order = order_mock()
    with mock.patch.object(oco_group.orders_manager, "get_order_from_group", mock.Mock(return_value=[order,
                                                                                                     other_order])) \
         as get_order_from_group_mock:
        await oco_group.on_cancel(order, ignored_orders=["hi"])
        order.trader.cancel_order.assert_not_called()
        other_order.trader.cancel_order.assert_called_once_with(other_order, ignored_order="hi")
        get_order_from_group_mock.assert_called_once_with(oco_group.name)
