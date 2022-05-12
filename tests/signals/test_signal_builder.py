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
import pytest

import octobot_trading.enums as enums
import octobot_trading.errors as errors
import octobot_trading.signals as signals

from tests import event_loop
from tests.exchanges import simulated_trader, simulated_exchange_manager
from tests.personal_data.orders import buy_limit_order

import octobot_trading.personal_data as personal_data


@pytest.fixture
def signal_builder():
    return signals.SignalBuilder(
        "strategy_name",
        "exchange_name",
        enums.ExchangeTypes.SPOT.value,
        "BTC/USDT",
        "signal description",
        enums.EvaluatorStates.SHORT.value,
        [],
    )


def test_build(signal_builder):
    trading_signal = signal_builder.build()
    assert trading_signal.strategy == "strategy_name"
    assert trading_signal.exchange == "exchange_name"
    assert trading_signal.exchange_type == enums.ExchangeTypes.SPOT.value
    assert trading_signal.symbol == "BTC/USDT"
    assert trading_signal.description == "signal description"
    assert trading_signal.state == enums.EvaluatorStates.SHORT.value
    assert trading_signal.orders == []

    signal_builder.orders = [None]
    assert signal_builder.build().orders == [None]


def test_reset(signal_builder):
    signal_builder.orders = ["hi"]
    signal_builder.reset()
    assert signal_builder.orders == []


def test_add_created_order(signal_builder, buy_limit_order):
    with pytest.raises(errors.InvalidArgumentError):
        signal_builder.add_created_order(buy_limit_order)
    signal_builder.add_created_order(buy_limit_order, target_amount="1%")
    assert len(signal_builder.orders) == 1
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.ACTION.value] \
        is enums.TradingSignalOrdersActions.CREATE.value
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.SHARED_SIGNAL_ORDER_ID.value] == \
           buy_limit_order.shared_signal_order_id
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] == "1%"
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] is None

    # add the same order: do not add it twice
    signal_builder.add_created_order(buy_limit_order, target_amount="1%")
    assert len(signal_builder.orders) == 1

    # update the same order
    buy_limit_order.order_type = enums.TraderOrderType.SELL_LIMIT
    signal_builder.add_created_order(buy_limit_order, target_position="2%")
    assert len(signal_builder.orders) == 1
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.SELL_LIMIT.value
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] is None
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] == "2%"

    # add new order (orders are based on shared_signal_order_id)
    previous_shared_signal_order_id= buy_limit_order.shared_signal_order_id
    buy_limit_order.set_shared_signal_order_id("other_id")
    buy_limit_order.order_type = enums.TraderOrderType.STOP_LOSS_LIMIT
    signal_builder.add_created_order(buy_limit_order, target_position="50")
    assert len(signal_builder.orders) == 2
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.SHARED_SIGNAL_ORDER_ID.value] == \
           previous_shared_signal_order_id
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.SELL_LIMIT.value
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] is None
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] == "2%"
    assert signal_builder.orders[1][enums.TradingSignalOrdersAttrs.SHARED_SIGNAL_ORDER_ID.value] == "other_id"
    assert signal_builder.orders[1][enums.TradingSignalOrdersAttrs.TYPE.value] == \
           enums.TraderOrderType.STOP_LOSS_LIMIT.value
    assert signal_builder.orders[1][enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] is None
    assert signal_builder.orders[1][enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] == "50"


def test_add_order_to_group(signal_builder, buy_limit_order):
    # no order_group
    signal_builder.add_order_to_group(buy_limit_order)
    # ensure properly added
    assert len(signal_builder.orders) == 1
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.ACTION.value] \
        is enums.TradingSignalOrdersActions.ADD_TO_GROUP.value
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.SHARED_SIGNAL_ORDER_ID.value] == \
           buy_limit_order.shared_signal_order_id
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] is None
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] is None

    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.GROUP_ID.value] is None
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.GROUP_TYPE.value] is None

    order_group = personal_data.OneCancelsTheOtherOrderGroup(
        "group_name",
        buy_limit_order.exchange_manager.exchange_personal_data.orders_manager
    )
    buy_limit_order.add_to_order_group(order_group)
    signal_builder.add_order_to_group(buy_limit_order)
    assert len(signal_builder.orders) == 1
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.GROUP_ID.value] == "group_name"
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.GROUP_TYPE.value] == \
           personal_data.OneCancelsTheOtherOrderGroup.__name__

    # add the same order: do not add it twice
    signal_builder.add_order_to_group(buy_limit_order)
    assert len(signal_builder.orders) == 1
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.GROUP_ID.value] == order_group.name
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.GROUP_TYPE.value] == order_group.__class__.__name__

    # update the same order
    other_order_group = personal_data.BalancedTakeProfitAndStopOrderGroup(
        "group_name_2",
        buy_limit_order.exchange_manager.exchange_personal_data.orders_manager
    )
    buy_limit_order.add_to_order_group(other_order_group)
    signal_builder.add_order_to_group(buy_limit_order)
    assert len(signal_builder.orders) == 1
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.GROUP_ID.value] == "group_name_2"
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.GROUP_TYPE.value] == \
           personal_data.BalancedTakeProfitAndStopOrderGroup.__name__

    # add new order (orders are based on shared_signal_order_id)
    buy_limit_order.set_shared_signal_order_id("other_id")
    buy_limit_order.add_to_order_group(order_group)
    signal_builder.add_order_to_group(buy_limit_order)
    assert len(signal_builder.orders) == 2
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.GROUP_ID.value] == "group_name_2"
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.GROUP_TYPE.value] == \
           personal_data.BalancedTakeProfitAndStopOrderGroup.__name__
    assert signal_builder.orders[1][enums.TradingSignalOrdersAttrs.GROUP_ID.value] == "group_name"
    assert signal_builder.orders[1][enums.TradingSignalOrdersAttrs.GROUP_TYPE.value] == \
           personal_data.OneCancelsTheOtherOrderGroup.__name__


def test_add_edited_order(signal_builder, buy_limit_order):
    # no updated argument
    with pytest.raises(errors.InvalidArgumentError):
        signal_builder.add_edited_order(buy_limit_order)

    signal_builder.add_edited_order(buy_limit_order, updated_target_amount="1%")
    # ensure properly added
    assert len(signal_builder.orders) == 1
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.ACTION.value] \
        is enums.TradingSignalOrdersActions.EDIT.value
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.SHARED_SIGNAL_ORDER_ID.value] == \
           buy_limit_order.shared_signal_order_id
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] == "1%"
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] is None
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_TARGET_AMOUNT.value] == "1%"
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_TARGET_POSITION.value] is None
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_LIMIT_PRICE.value] == 0.0
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_STOP_PRICE.value] == 0.0
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_CURRENT_PRICE.value] == 0.0

    # add the same order: do not add it twice, update existing order
    signal_builder.add_edited_order(buy_limit_order, updated_target_position="1%")
    assert len(signal_builder.orders) == 1
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] is None
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] == "1%"
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_TARGET_AMOUNT.value] is None
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_TARGET_POSITION.value] == "1%"
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_LIMIT_PRICE.value] == 0.0
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_STOP_PRICE.value] == 0.0
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_CURRENT_PRICE.value] == 0.0
    signal_builder.add_edited_order(buy_limit_order, updated_limit_price=decimal.Decimal("1"))
    assert len(signal_builder.orders) == 1
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] is None
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] is None
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_TARGET_AMOUNT.value] is None
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_TARGET_POSITION.value] is None
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_LIMIT_PRICE.value] == 1.0
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_STOP_PRICE.value] == 0.0
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_CURRENT_PRICE.value] == 0.0
    signal_builder.add_edited_order(buy_limit_order, updated_stop_price=decimal.Decimal("1"))
    assert len(signal_builder.orders) == 1
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] is None
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] is None
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_TARGET_AMOUNT.value] is None
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_TARGET_POSITION.value] is None
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_LIMIT_PRICE.value] == 0.0
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_STOP_PRICE.value] == 1.0
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_CURRENT_PRICE.value] == 0.0
    signal_builder.add_edited_order(buy_limit_order, updated_current_price=decimal.Decimal("1"))
    assert len(signal_builder.orders) == 1
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value] is None
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TARGET_POSITION.value] is None
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_TARGET_AMOUNT.value] is None
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_TARGET_POSITION.value] is None
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_LIMIT_PRICE.value] == 0.0
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_STOP_PRICE.value] == 0.0
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_CURRENT_PRICE.value] == 1.0

    # add new order (orders are based on shared_signal_order_id)
    buy_limit_order.set_shared_signal_order_id("other_id")
    signal_builder.add_edited_order(buy_limit_order, updated_target_position="1%a")
    assert len(signal_builder.orders) == 2
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_CURRENT_PRICE.value] == 1.0
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.UPDATED_TARGET_POSITION.value] == None
    assert signal_builder.orders[1][enums.TradingSignalOrdersAttrs.UPDATED_CURRENT_PRICE.value] == 0.0
    assert signal_builder.orders[1][enums.TradingSignalOrdersAttrs.UPDATED_TARGET_POSITION.value] == "1%a"


def test_add_cancelled_order(signal_builder, buy_limit_order):
    signal_builder.add_cancelled_order(buy_limit_order)
    assert len(signal_builder.orders) == 1
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.ACTION.value] \
        is enums.TradingSignalOrdersActions.CANCEL.value
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.SHARED_SIGNAL_ORDER_ID.value] == \
           buy_limit_order.shared_signal_order_id

    # add the same order: do not add it twice
    signal_builder.add_cancelled_order(buy_limit_order)
    assert len(signal_builder.orders) == 1

    # add new order (orders are based on shared_signal_order_id)
    buy_limit_order.set_shared_signal_order_id("other_id")
    buy_limit_order.order_type = enums.TraderOrderType.STOP_LOSS_LIMIT
    signal_builder.add_created_order(buy_limit_order, target_position="50")
    assert len(signal_builder.orders) == 2
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert signal_builder.orders[1][enums.TradingSignalOrdersAttrs.TYPE.value] == \
           enums.TraderOrderType.STOP_LOSS_LIMIT.value

    # add an orders via create action: it gets popped out of the orders list as there is no point creating
    # it and cancelling it right away
    buy_limit_order.set_shared_signal_order_id("buy_other_id")
    buy_limit_order.order_type = enums.TraderOrderType.BUY_MARKET
    signal_builder.add_created_order(buy_limit_order, target_amount="1")
    assert len(signal_builder.orders) == 3
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert signal_builder.orders[1][enums.TradingSignalOrdersAttrs.TYPE.value] == \
           enums.TraderOrderType.STOP_LOSS_LIMIT.value
    assert signal_builder.orders[2][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_MARKET.value

    # BUY_MARKET order got removed from orders
    signal_builder.add_cancelled_order(buy_limit_order)
    assert len(signal_builder.orders) == 2
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert signal_builder.orders[1][enums.TradingSignalOrdersAttrs.TYPE.value] == \
           enums.TraderOrderType.STOP_LOSS_LIMIT.value

    # adding BUY_MARKET as add to group order
    other_order_group = personal_data.BalancedTakeProfitAndStopOrderGroup(
        "group_name_2",
        buy_limit_order.exchange_manager.exchange_personal_data.orders_manager
    )
    buy_limit_order.add_to_order_group(other_order_group)
    signal_builder.add_order_to_group(buy_limit_order)
    assert len(signal_builder.orders) == 3
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert signal_builder.orders[1][enums.TradingSignalOrdersAttrs.TYPE.value] == \
           enums.TraderOrderType.STOP_LOSS_LIMIT.value
    assert signal_builder.orders[2][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_MARKET.value
    assert signal_builder.orders[2][enums.TradingSignalOrdersAttrs.ACTION.value] == \
           enums.TradingSignalOrdersActions.ADD_TO_GROUP.value

    # BUY_MARKET order sill in order but action is not cancel from orders
    signal_builder.add_cancelled_order(buy_limit_order)
    assert len(signal_builder.orders) == 3
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert signal_builder.orders[1][enums.TradingSignalOrdersAttrs.TYPE.value] == \
           enums.TraderOrderType.STOP_LOSS_LIMIT.value
    assert signal_builder.orders[2][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_MARKET.value
    assert signal_builder.orders[2][enums.TradingSignalOrdersAttrs.ACTION.value] == \
           enums.TradingSignalOrdersActions.CANCEL.value

    # adding BUY_MARKET as edited order
    buy_limit_order.set_shared_signal_order_id("edit_buy_other_id")
    signal_builder.add_edited_order(buy_limit_order, updated_target_amount="1")
    assert len(signal_builder.orders) == 4
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert signal_builder.orders[1][enums.TradingSignalOrdersAttrs.TYPE.value] == \
           enums.TraderOrderType.STOP_LOSS_LIMIT.value
    assert signal_builder.orders[2][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_MARKET.value
    assert signal_builder.orders[2][enums.TradingSignalOrdersAttrs.ACTION.value] == \
           enums.TradingSignalOrdersActions.CANCEL.value
    assert signal_builder.orders[3][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_MARKET.value
    assert signal_builder.orders[3][enums.TradingSignalOrdersAttrs.ACTION.value] == \
           enums.TradingSignalOrdersActions.EDIT.value

    # BUY_MARKET order sill in order but action is not cancel from orders
    signal_builder.add_cancelled_order(buy_limit_order)
    assert len(signal_builder.orders) == 4
    assert signal_builder.orders[0][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_LIMIT.value
    assert signal_builder.orders[1][enums.TradingSignalOrdersAttrs.TYPE.value] == \
           enums.TraderOrderType.STOP_LOSS_LIMIT.value
    assert signal_builder.orders[2][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_MARKET.value
    assert signal_builder.orders[2][enums.TradingSignalOrdersAttrs.ACTION.value] == \
           enums.TradingSignalOrdersActions.CANCEL.value
    assert signal_builder.orders[3][enums.TradingSignalOrdersAttrs.TYPE.value] == enums.TraderOrderType.BUY_MARKET.value
    assert signal_builder.orders[3][enums.TradingSignalOrdersAttrs.ACTION.value] == \
           enums.TradingSignalOrdersActions.CANCEL.value
