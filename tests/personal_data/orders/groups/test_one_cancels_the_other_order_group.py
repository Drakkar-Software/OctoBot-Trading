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
import octobot_trading.errors as errors
import octobot_trading.enums as enums
import octobot_trading.constants as constants
import octobot_commons.asyncio_tools as asyncio_tools
from tests.personal_data import DEFAULT_ORDER_SYMBOL
from tests.personal_data.orders.groups import order_mock
from tests.personal_data.orders import created_order
from tests.exchanges import simulated_trader, simulated_exchange_manager
import tests.test_utils.random_numbers as random_numbers


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


@pytest.fixture
def oco_group():
    orders_manager = mock.Mock()
    orders_manager.get_order_from_group = mock.Mock()
    return personal_data.OneCancelsTheOtherOrderGroup("name",  orders_manager)


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
        other_order.trader.cancel_order.assert_called_once_with(
            other_order, ignored_order=order, wait_for_cancelling=True,
            cancelling_timeout=constants.INDIVIDUAL_ORDER_SYNC_TIMEOUT
        )
        get_order_from_group_mock.assert_called_once_with(oco_group.name)


async def test_on_fill_no_mock(simulated_trader):
    _, exchange_manager, trader_instance = simulated_trader
    oco_group = personal_data.OneCancelsTheOtherOrderGroup("name",
                                                           exchange_manager.exchange_personal_data.orders_manager)
    stop_loss = created_order(personal_data.StopLossLimitOrder, enums.TraderOrderType.STOP_LOSS,
                              trader_instance, side=enums.TradeOrderSide.SELL)
    stop_loss.update(
        price=decimal.Decimal(10),
        quantity=decimal.Decimal(1),
        symbol=DEFAULT_ORDER_SYMBOL,
        order_type=enums.TraderOrderType.STOP_LOSS,
        group=oco_group,
    )
    sell_limit = created_order(personal_data.SellLimitOrder, enums.TraderOrderType.SELL_LIMIT,
                               trader_instance, side=enums.TradeOrderSide.SELL)
    sell_limit.update(
        price=decimal.Decimal(20),
        quantity=decimal.Decimal(1),
        symbol=DEFAULT_ORDER_SYMBOL,
        order_type=enums.TraderOrderType.SELL_LIMIT,
        group=oco_group,
    )

    for order in [stop_loss, sell_limit]:
        order.exchange_manager.is_backtesting = True  # force update_order_status
        await order.initialize()
        await order.exchange_manager.exchange_personal_data.orders_manager.upsert_order_instance(
            order
        )
    price_events_manager = stop_loss.exchange_manager.exchange_symbols_data.get_exchange_symbol_data(
        DEFAULT_ORDER_SYMBOL).price_events_manager
    # stop loss sell order triggers when price is bellow or equal to its trigger price
    price_events_manager.handle_recent_trades(
        [random_numbers.decimal_random_recent_trade(price=decimal.Decimal(9), timestamp=stop_loss.timestamp)]
    )
    # simulate a real-trader order (that is self-managed therefore an exchange update is not required)
    stop_loss.simulated = False

    # fill stop loss and cancel sell limit
    await asyncio_tools.wait_asyncio_next_cycle()
    assert stop_loss.is_filled()
    assert sell_limit.is_cancelled()


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
        other_order.trader.cancel_order.assert_called_once_with(
            other_order, ignored_order="hi", wait_for_cancelling=True,
            cancelling_timeout=constants.INDIVIDUAL_ORDER_SYNC_TIMEOUT
        )
        get_order_from_group_mock.assert_called_once_with(oco_group.name)
