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
import copy
import decimal

import mock
import pytest

import octobot_trading.enums as enums
import octobot_trading.errors as errors
import octobot_trading.signals as signals

from tests import event_loop
from tests.exchanges import simulated_trader, simulated_exchange_manager
from tests.personal_data.orders import buy_limit_order, sell_limit_order, stop_loss_limit_order, stop_loss_buy_order

import octobot_trading.personal_data as personal_data


@pytest.fixture
def trading_signal_bundle_builder():
    builder = signals.TradingSignalBundleBuilder(
        "identifier",
        "strategy_name",
    )
    builder.logger = mock.Mock(debug=mock.Mock(), error=mock.Mock())
    return builder


def test_build(trading_signal_bundle_builder):
    with mock.patch.object(trading_signal_bundle_builder, "_pack_referenced_orders_together", mock.Mock()) \
         as _pack_referenced_orders_together_mock:
        trading_signal_bundle = trading_signal_bundle_builder.build()
        assert trading_signal_bundle.identifier == "identifier"
        assert trading_signal_bundle.signals == []
        _pack_referenced_orders_together_mock.assert_called_once()


def test_sort(trading_signal_bundle_builder, buy_limit_order):
    assert trading_signal_bundle_builder.signals == []
    assert trading_signal_bundle_builder.sort_signals().signals == []
    order_ids = [
        f"order_id_{i}"
        for i in range(5)
    ]
    buy_limit_order.order_id = order_ids[0]
    trading_signal_bundle_builder.add_created_order(buy_limit_order, buy_limit_order.exchange_manager, target_amount="1%")
    # add new order (orders are based on order_id)
    buy_limit_order.order_id = order_ids[1]
    trading_signal_bundle_builder.add_cancelled_order(buy_limit_order, buy_limit_order.exchange_manager)
    buy_limit_order.order_id = order_ids[2]
    trading_signal_bundle_builder.add_cancelled_order(buy_limit_order, buy_limit_order.exchange_manager)
    buy_limit_order.order_id = order_ids[3]
    trading_signal_bundle_builder.add_created_order(buy_limit_order, buy_limit_order.exchange_manager, target_amount="2%")
    buy_limit_order.order_id = order_ids[4]
    trading_signal_bundle_builder.add_created_order(buy_limit_order, buy_limit_order.exchange_manager, target_amount="3%")

    origin_signals = copy.copy(trading_signal_bundle_builder.signals)
    assert order_ids == [signal.content[enums.TradingSignalOrdersAttrs.ORDER_ID.value] for signal in origin_signals]
    builder = trading_signal_bundle_builder.sort_signals()
    assert builder is trading_signal_bundle_builder
    sorted_signals = builder.signals
    sorted_ids = [order_ids[1], order_ids[2], order_ids[0], order_ids[3], order_ids[4]]
    assert sorted_ids == [signal.content[enums.TradingSignalOrdersAttrs.ORDER_ID.value] for signal in sorted_signals]


def test_add_created_order(trading_signal_bundle_builder, buy_limit_order):
    with pytest.raises(errors.InvalidArgumentError):
        trading_signal_bundle_builder.add_created_order(buy_limit_order, buy_limit_order.exchange_manager)
    trading_signal_bundle_builder.add_created_order(buy_limit_order, buy_limit_order.exchange_manager, target_amount="1%")
    assert len(trading_signal_bundle_builder.signals) == 1
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalCommonsAttrs.ACTION.value] \
           is enums.TradingSignalOrdersActions.CREATE.value
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.ORDER_ID.value] == \
           buy_limit_order.order_id
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] == "1%"
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] is None

    # add the same order: do not add it twice
    trading_signal_bundle_builder.add_created_order(buy_limit_order, buy_limit_order.exchange_manager, target_amount="1%")
    assert len(trading_signal_bundle_builder.signals) == 1

    # update the same order
    buy_limit_order.order_type = enums.TraderOrderType.SELL_LIMIT
    trading_signal_bundle_builder.add_created_order(buy_limit_order, buy_limit_order.exchange_manager, target_position="2%")
    assert len(trading_signal_bundle_builder.signals) == 1
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.SELL_LIMIT.value
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] is None
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] == "2%"

    # add new order (orders are based on order_id)
    previous_order_id = buy_limit_order.order_id
    buy_limit_order.order_id = "other_id"
    buy_limit_order.order_type = enums.TraderOrderType.STOP_LOSS_LIMIT
    trading_signal_bundle_builder.add_created_order(buy_limit_order, buy_limit_order.exchange_manager, target_position="50")
    assert len(trading_signal_bundle_builder.signals) == 2
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.ORDER_ID.value] == \
           previous_order_id
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.SELL_LIMIT.value
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] is None
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] == "2%"
    assert trading_signal_bundle_builder.signals[1].content[enums.TradingSignalOrdersAttrs.ORDER_ID.value] == "other_id"
    assert trading_signal_bundle_builder.signals[1].content[enums.TradingSignalOrdersAttrs.TYPE.value] == \
           enums.TraderOrderType.STOP_LOSS_LIMIT.value
    assert trading_signal_bundle_builder.signals[1].content[enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] is None
    assert trading_signal_bundle_builder.signals[1].content[enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] == "50"


def test_add_order_to_group(trading_signal_bundle_builder, buy_limit_order):
    # no order_group
    trading_signal_bundle_builder.add_order_to_group(buy_limit_order, buy_limit_order.exchange_manager)
    # ensure properly added
    assert len(trading_signal_bundle_builder.signals) == 1
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalCommonsAttrs.ACTION.value] \
           is enums.TradingSignalOrdersActions.ADD_TO_GROUP.value
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.ORDER_ID.value] == \
           buy_limit_order.order_id
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] is None
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] is None

    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.GROUP_ID.value] is None
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.GROUP_TYPE.value] is None

    order_group = personal_data.OneCancelsTheOtherOrderGroup(
        "group_name",
        buy_limit_order.exchange_manager.exchange_personal_data.orders_manager
    )
    buy_limit_order.add_to_order_group(order_group)
    trading_signal_bundle_builder.add_order_to_group(buy_limit_order, buy_limit_order.exchange_manager)
    assert len(trading_signal_bundle_builder.signals) == 1
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.GROUP_ID.value] == "group_name"
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.GROUP_TYPE.value] == \
           personal_data.OneCancelsTheOtherOrderGroup.__name__

    # add the same order: do not add it twice
    trading_signal_bundle_builder.add_order_to_group(buy_limit_order, buy_limit_order.exchange_manager)
    assert len(trading_signal_bundle_builder.signals) == 1
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.GROUP_ID.value] == order_group.name
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.GROUP_TYPE.value] == order_group.__class__.__name__

    # update the same order
    other_order_group = personal_data.BalancedTakeProfitAndStopOrderGroup(
        "group_name_2",
        buy_limit_order.exchange_manager.exchange_personal_data.orders_manager
    )
    buy_limit_order.add_to_order_group(other_order_group)
    trading_signal_bundle_builder.add_order_to_group(buy_limit_order, buy_limit_order.exchange_manager)
    assert len(trading_signal_bundle_builder.signals) == 1
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.GROUP_ID.value] == "group_name_2"
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.GROUP_TYPE.value] == \
           personal_data.BalancedTakeProfitAndStopOrderGroup.__name__

    # add new order (orders are based on order_id)
    buy_limit_order.order_id = "other_id"
    buy_limit_order.add_to_order_group(order_group)
    trading_signal_bundle_builder.add_order_to_group(buy_limit_order, buy_limit_order.exchange_manager)
    assert len(trading_signal_bundle_builder.signals) == 2
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.GROUP_ID.value] == "group_name_2"
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.GROUP_TYPE.value] == \
           personal_data.BalancedTakeProfitAndStopOrderGroup.__name__
    assert trading_signal_bundle_builder.signals[1].content[enums.TradingSignalOrdersAttrs.GROUP_ID.value] == "group_name"
    assert trading_signal_bundle_builder.signals[1].content[enums.TradingSignalOrdersAttrs.GROUP_TYPE.value] == \
           personal_data.OneCancelsTheOtherOrderGroup.__name__


def test_add_edited_order(trading_signal_bundle_builder, buy_limit_order):
    # no updated argument
    with pytest.raises(errors.InvalidArgumentError):
        trading_signal_bundle_builder.add_edited_order(buy_limit_order, buy_limit_order.exchange_manager)

    trading_signal_bundle_builder.add_edited_order(buy_limit_order, buy_limit_order.exchange_manager, updated_target_amount="1%")
    # ensure properly added
    assert len(trading_signal_bundle_builder.signals) == 1
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalCommonsAttrs.ACTION.value] \
           is enums.TradingSignalOrdersActions.EDIT.value
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.ORDER_ID.value] == \
           buy_limit_order.order_id
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] == "1%"
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] is None
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_TARGET_AMOUNT.value] == "1%"
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_TARGET_POSITION.value] is None
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_LIMIT_PRICE.value] == 0.0
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_STOP_PRICE.value] == 0.0
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_CURRENT_PRICE.value] == 0.0

    # add the same order: do not add it twice, update existing order
    trading_signal_bundle_builder.add_edited_order(buy_limit_order, buy_limit_order.exchange_manager, updated_target_position="1%")
    assert len(trading_signal_bundle_builder.signals) == 1
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] is None
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] == "1%"
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_TARGET_AMOUNT.value] is None
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_TARGET_POSITION.value] == "1%"
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_LIMIT_PRICE.value] == 0.0
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_STOP_PRICE.value] == 0.0
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_CURRENT_PRICE.value] == 0.0
    trading_signal_bundle_builder.add_edited_order(buy_limit_order, buy_limit_order.exchange_manager, updated_limit_price=decimal.Decimal("1"))
    assert len(trading_signal_bundle_builder.signals) == 1
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] is None
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] is None
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_TARGET_AMOUNT.value] is None
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_TARGET_POSITION.value] is None
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_LIMIT_PRICE.value] == 1.0
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_STOP_PRICE.value] == 0.0
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_CURRENT_PRICE.value] == 0.0
    trading_signal_bundle_builder.add_edited_order(buy_limit_order, buy_limit_order.exchange_manager, updated_stop_price=decimal.Decimal("1"))
    assert len(trading_signal_bundle_builder.signals) == 1
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] is None
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] is None
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_TARGET_AMOUNT.value] is None
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_TARGET_POSITION.value] is None
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_LIMIT_PRICE.value] == 0.0
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_STOP_PRICE.value] == 1.0
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_CURRENT_PRICE.value] == 0.0
    trading_signal_bundle_builder.add_edited_order(buy_limit_order, buy_limit_order.exchange_manager, updated_current_price=decimal.Decimal("1"))
    assert len(trading_signal_bundle_builder.signals) == 1
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] is None
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] is None
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_TARGET_AMOUNT.value] is None
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_TARGET_POSITION.value] is None
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_LIMIT_PRICE.value] == 0.0
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_STOP_PRICE.value] == 0.0
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_CURRENT_PRICE.value] == 1.0

    # add new order (orders are based on order_id)
    buy_limit_order.order_id = "other_id"
    trading_signal_bundle_builder.add_edited_order(buy_limit_order, buy_limit_order.exchange_manager, updated_target_position="1%a")
    assert len(trading_signal_bundle_builder.signals) == 2
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_CURRENT_PRICE.value] == 1.0
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.UPDATED_TARGET_POSITION.value] == None
    assert trading_signal_bundle_builder.signals[1].content[enums.TradingSignalOrdersAttrs.UPDATED_CURRENT_PRICE.value] == 0.0
    assert trading_signal_bundle_builder.signals[1].content[enums.TradingSignalOrdersAttrs.UPDATED_TARGET_POSITION.value] == "1%a"


@pytest.mark.asyncio
async def test_add_cancelled_order(trading_signal_bundle_builder, buy_limit_order):
    trading_signal_bundle_builder.add_cancelled_order(buy_limit_order, buy_limit_order.exchange_manager)
    assert len(trading_signal_bundle_builder.signals) == 1
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalCommonsAttrs.ACTION.value] \
           is enums.TradingSignalOrdersActions.CANCEL.value
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.ORDER_ID.value] == \
           buy_limit_order.order_id

    # add the same order: do not add it twice
    trading_signal_bundle_builder.add_cancelled_order(buy_limit_order, buy_limit_order.exchange_manager)
    assert len(trading_signal_bundle_builder.signals) == 1

    # add new order (orders are based on order_id)
    # cancel order first to be sure it can be added
    exchange_manager = buy_limit_order.exchange_manager
    await buy_limit_order.exchange_manager.trader.cancel_order(buy_limit_order)
    buy_limit_order.clear()
    buy_limit_order.order_id = "other_id"
    buy_limit_order.order_type = enums.TraderOrderType.STOP_LOSS_LIMIT
    trading_signal_bundle_builder.add_created_order(buy_limit_order, exchange_manager, target_position="50")
    assert len(trading_signal_bundle_builder.signals) == 2
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert trading_signal_bundle_builder.signals[1].content[enums.TradingSignalOrdersAttrs.TYPE.value] == \
           enums.TraderOrderType.STOP_LOSS_LIMIT.value

    # add an orders via create action: it gets popped out of the orders list as there is no point creating
    # it and cancelling it right away
    buy_limit_order.order_id = "buy_other_id"
    buy_limit_order.order_type = enums.TraderOrderType.BUY_MARKET
    trading_signal_bundle_builder.add_created_order(buy_limit_order, exchange_manager, target_amount="1")
    assert len(trading_signal_bundle_builder.signals) == 3
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert trading_signal_bundle_builder.signals[1].content[enums.TradingSignalOrdersAttrs.TYPE.value] == \
           enums.TraderOrderType.STOP_LOSS_LIMIT.value
    assert trading_signal_bundle_builder.signals[2].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_MARKET.value

    # BUY_MARKET order got removed from orders
    trading_signal_bundle_builder.add_cancelled_order(buy_limit_order, exchange_manager)
    assert len(trading_signal_bundle_builder.signals) == 2
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert trading_signal_bundle_builder.signals[1].content[enums.TradingSignalOrdersAttrs.TYPE.value] == \
           enums.TraderOrderType.STOP_LOSS_LIMIT.value

    # adding BUY_MARKET as add to group order
    other_order_group = personal_data.BalancedTakeProfitAndStopOrderGroup(
        "group_name_2",
        exchange_manager.exchange_personal_data.orders_manager
    )
    buy_limit_order.add_to_order_group(other_order_group)
    trading_signal_bundle_builder.add_order_to_group(buy_limit_order, exchange_manager)
    assert len(trading_signal_bundle_builder.signals) == 3
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert trading_signal_bundle_builder.signals[1].content[enums.TradingSignalOrdersAttrs.TYPE.value] == \
           enums.TraderOrderType.STOP_LOSS_LIMIT.value
    assert trading_signal_bundle_builder.signals[2].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_MARKET.value
    assert trading_signal_bundle_builder.signals[2].content[enums.TradingSignalCommonsAttrs.ACTION.value] == \
           enums.TradingSignalOrdersActions.ADD_TO_GROUP.value

    # BUY_MARKET order sill in order but action is not cancel from orders
    trading_signal_bundle_builder.add_cancelled_order(buy_limit_order, exchange_manager)
    assert len(trading_signal_bundle_builder.signals) == 3
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert trading_signal_bundle_builder.signals[1].content[enums.TradingSignalOrdersAttrs.TYPE.value] == \
           enums.TraderOrderType.STOP_LOSS_LIMIT.value
    assert trading_signal_bundle_builder.signals[2].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_MARKET.value
    assert trading_signal_bundle_builder.signals[2].content[enums.TradingSignalCommonsAttrs.ACTION.value] == \
           enums.TradingSignalOrdersActions.CANCEL.value

    # adding BUY_MARKET as edited order
    buy_limit_order.order_id = "edit_buy_other_id"
    trading_signal_bundle_builder.add_edited_order(buy_limit_order, exchange_manager, updated_target_amount="1")
    assert len(trading_signal_bundle_builder.signals) == 4
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert trading_signal_bundle_builder.signals[1].content[enums.TradingSignalOrdersAttrs.TYPE.value] == \
           enums.TraderOrderType.STOP_LOSS_LIMIT.value
    assert trading_signal_bundle_builder.signals[2].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_MARKET.value
    assert trading_signal_bundle_builder.signals[2].content[enums.TradingSignalCommonsAttrs.ACTION.value] == \
           enums.TradingSignalOrdersActions.CANCEL.value
    assert trading_signal_bundle_builder.signals[3].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_MARKET.value
    assert trading_signal_bundle_builder.signals[3].content[enums.TradingSignalCommonsAttrs.ACTION.value] == \
           enums.TradingSignalOrdersActions.EDIT.value

    # BUY_MARKET order sill in order but action is not cancel from orders
    trading_signal_bundle_builder.add_cancelled_order(buy_limit_order, exchange_manager)
    assert len(trading_signal_bundle_builder.signals) == 4
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert trading_signal_bundle_builder.signals[1].content[enums.TradingSignalOrdersAttrs.TYPE.value] == \
           enums.TraderOrderType.STOP_LOSS_LIMIT.value
    assert trading_signal_bundle_builder.signals[2].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_MARKET.value
    assert trading_signal_bundle_builder.signals[2].content[enums.TradingSignalCommonsAttrs.ACTION.value] == \
           enums.TradingSignalOrdersActions.CANCEL.value
    assert trading_signal_bundle_builder.signals[3].content[enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_MARKET.value
    assert trading_signal_bundle_builder.signals[3].content[enums.TradingSignalCommonsAttrs.ACTION.value] == \
           enums.TradingSignalOrdersActions.CANCEL.value


def test_pack_referenced_orders_together(trading_signal_bundle_builder,
                                         buy_limit_order, sell_limit_order, stop_loss_limit_order, stop_loss_buy_order):
    buy_limit_order.order_id = "0"
    sell_limit_order.order_id = "1"
    stop_loss_limit_order.order_id = "2"
    trading_signal_bundle_builder.add_created_order(buy_limit_order, buy_limit_order.exchange_manager, target_amount="1%")
    trading_signal_bundle_builder.add_created_order(sell_limit_order, buy_limit_order.exchange_manager, target_amount="1%")
    trading_signal_bundle_builder.add_created_order(stop_loss_limit_order, buy_limit_order.exchange_manager, target_amount="1%")
    assert len(trading_signal_bundle_builder.signals) == 3
    assert all(signal.content[enums.TradingSignalOrdersAttrs.ADDITIONAL_ORDERS.value] == []
               for signal in trading_signal_bundle_builder.signals)
    pre_pack_signals = copy.copy(trading_signal_bundle_builder.signals)
    trading_signal_bundle_builder._pack_referenced_orders_together()
    # no order to be packed, no change
    assert len(trading_signal_bundle_builder.signals) == 3
    assert all(signal.content[enums.TradingSignalOrdersAttrs.ADDITIONAL_ORDERS.value] == []
               for signal in trading_signal_bundle_builder.signals)

    # missing id
    trading_signal_bundle_builder.logger.debug.assert_not_called()
    pre_pack_signals[2].content[enums.TradingSignalOrdersAttrs.BUNDLED_WITH.value] = "11"
    trading_signal_bundle_builder._pack_referenced_orders_together()
    trading_signal_bundle_builder.logger.debug.assert_called_once()
    assert "triggering order not found" in trading_signal_bundle_builder.logger.debug.call_args[0][0]
    trading_signal_bundle_builder.logger.debug.reset_mock()
    # no signals update
    assert trading_signal_bundle_builder.signals == pre_pack_signals

    # bundle stop loss with buy limit
    pre_pack_signals[2].content[enums.TradingSignalOrdersAttrs.BUNDLED_WITH.value] = "0"
    trading_signal_bundle_builder._pack_referenced_orders_together()
    # no order to be packed, no change
    assert len(trading_signal_bundle_builder.signals) == 2
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.ADDITIONAL_ORDERS.value][0] \
           is pre_pack_signals[2].content
    assert trading_signal_bundle_builder.signals[1].content[enums.TradingSignalOrdersAttrs.ADDITIONAL_ORDERS.value] \
           == []
    trading_signal_bundle_builder.logger.debug.assert_not_called()

    # reset signals
    trading_signal_bundle_builder.signals = pre_pack_signals
    for signal in trading_signal_bundle_builder.signals:
        signal.content[enums.TradingSignalOrdersAttrs.ADDITIONAL_ORDERS.value] = []
    # also chain sell limit to buy limit
    pre_pack_signals[1].content[enums.TradingSignalOrdersAttrs.CHAINED_TO.value] = "0"
    trading_signal_bundle_builder._pack_referenced_orders_together()
    assert len(trading_signal_bundle_builder.signals) == 1
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.ADDITIONAL_ORDERS.value][0] \
           is pre_pack_signals[1].content
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.ADDITIONAL_ORDERS.value][1] \
           is pre_pack_signals[2].content
    trading_signal_bundle_builder.logger.debug.assert_not_called()

    # reset signals
    trading_signal_bundle_builder.signals = pre_pack_signals
    for signal in trading_signal_bundle_builder.signals:
        signal.content[enums.TradingSignalOrdersAttrs.ADDITIONAL_ORDERS.value] = []
    # also chain sell limit to buy limit
    pre_pack_signals[1].content[enums.TradingSignalOrdersAttrs.CHAINED_TO.value] = "0"
    trading_signal_bundle_builder._pack_referenced_orders_together()
    assert len(trading_signal_bundle_builder.signals) == 1
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.ADDITIONAL_ORDERS.value][0] \
           is pre_pack_signals[1].content
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.ADDITIONAL_ORDERS.value][1] \
           is pre_pack_signals[2].content
    trading_signal_bundle_builder.logger.debug.assert_not_called()

    # reset signals
    trading_signal_bundle_builder.signals = pre_pack_signals
    for signal in trading_signal_bundle_builder.signals:
        signal.content[enums.TradingSignalOrdersAttrs.ADDITIONAL_ORDERS.value] = []
    # add stop_loss_buy_order in the same group as stop_loss_sell_order
    trading_signal_bundle_builder.add_created_order(stop_loss_buy_order, buy_limit_order.exchange_manager, target_amount="1%")
    trading_signal_bundle_builder.signals[2].content[enums.TradingSignalOrdersAttrs.BUNDLED_WITH.value] = None
    trading_signal_bundle_builder.signals[2].content[enums.TradingSignalOrdersAttrs.GROUP_ID.value] = "grp"
    trading_signal_bundle_builder.signals[3].content[enums.TradingSignalOrdersAttrs.GROUP_ID.value] = "grp"
    pre_pack_signals = copy.copy(trading_signal_bundle_builder.signals)
    trading_signal_bundle_builder._pack_referenced_orders_together()
    trading_signal_bundle_builder.logger.debug.assert_not_called()
    assert len(trading_signal_bundle_builder.signals) == 2
    assert trading_signal_bundle_builder.signals[0].content[enums.TradingSignalOrdersAttrs.ADDITIONAL_ORDERS.value][0] \
           is pre_pack_signals[1].content
    assert trading_signal_bundle_builder.signals[1].content[enums.TradingSignalOrdersAttrs.ADDITIONAL_ORDERS.value][0] \
           is pre_pack_signals[3].content
    
    trading_signal_bundle_builder.logger.error.assert_not_called()
