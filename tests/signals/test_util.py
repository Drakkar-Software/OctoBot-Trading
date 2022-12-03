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
import octobot_trading.signals as signals

from tests import event_loop
from tests.exchanges import simulated_trader, simulated_exchange_manager
from tests.personal_data.orders import buy_limit_order, sell_limit_order

import octobot_trading.personal_data as personal_data


@pytest.mark.asyncio
async def test_create_order_signal_description(buy_limit_order, sell_limit_order):
    buy_limit_order.reduce_only = True
    buy_limit_order.tag = "hello"
    buy_limit_order.symbol = "BTC/ETH"
    buy_limit_order.origin_price = decimal.Decimal("1.11")
    buy_limit_order.origin_quantity = decimal.Decimal("1.12")
    buy_limit_order.origin_stop_price = decimal.Decimal("1.13")
    exchange_manager = buy_limit_order.exchange_manager
    assert signals.create_order_signal_content(buy_limit_order, enums.TradingSignalOrdersActions.CREATE,
                                               "strat", exchange_manager) == {
        enums.TradingSignalCommonsAttrs.ACTION.value: enums.TradingSignalOrdersActions.CREATE.value,
        enums.TradingSignalOrdersAttrs.SIDE.value: enums.TradeOrderSide.BUY.value,
        enums.TradingSignalOrdersAttrs.STRATEGY.value: "strat",
        enums.TradingSignalOrdersAttrs.SYMBOL.value: "BTC/ETH",
        enums.TradingSignalOrdersAttrs.EXCHANGE.value: "binanceus",
        enums.TradingSignalOrdersAttrs.EXCHANGE_TYPE.value: enums.ExchangeTypes.SPOT.value,
        enums.TradingSignalOrdersAttrs.TYPE.value: enums.TraderOrderType.BUY_LIMIT.value,
        enums.TradingSignalOrdersAttrs.QUANTITY.value: float(buy_limit_order.origin_quantity),
        enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value: None,
        enums.TradingSignalOrdersAttrs.TARGET_POSITION.value: None,
        enums.TradingSignalOrdersAttrs.UPDATED_TARGET_AMOUNT.value: None,
        enums.TradingSignalOrdersAttrs.UPDATED_TARGET_POSITION.value: None,
        enums.TradingSignalOrdersAttrs.LIMIT_PRICE.value: float(buy_limit_order.origin_price),
        enums.TradingSignalOrdersAttrs.UPDATED_LIMIT_PRICE.value: 0.0,
        enums.TradingSignalOrdersAttrs.STOP_PRICE.value: float(buy_limit_order.origin_stop_price),
        enums.TradingSignalOrdersAttrs.UPDATED_STOP_PRICE.value: 0.0,
        enums.TradingSignalOrdersAttrs.CURRENT_PRICE.value: float(buy_limit_order.created_last_price),
        enums.TradingSignalOrdersAttrs.UPDATED_CURRENT_PRICE.value: 0.0,
        enums.TradingSignalOrdersAttrs.REDUCE_ONLY.value: True,
        enums.TradingSignalOrdersAttrs.POST_ONLY.value: False,
        enums.TradingSignalOrdersAttrs.GROUP_ID.value: None,
        enums.TradingSignalOrdersAttrs.GROUP_TYPE.value: None,
        enums.TradingSignalOrdersAttrs.TAG.value: "hello",
        enums.TradingSignalOrdersAttrs.SHARED_SIGNAL_ORDER_ID.value: buy_limit_order.shared_signal_order_id,
        enums.TradingSignalOrdersAttrs.BUNDLED_WITH.value: None,
        enums.TradingSignalOrdersAttrs.CHAINED_TO.value: None,
        enums.TradingSignalOrdersAttrs.ADDITIONAL_ORDERS.value: [],
    }

    sell_limit_order.add_chained_order(buy_limit_order)
    sell_limit_order.symbol = "BTC/ETH"
    await buy_limit_order.set_as_chained_order(sell_limit_order, True, {})
    assert signals.create_order_signal_content(
        buy_limit_order,
        enums.TradingSignalOrdersActions.CREATE,
        "strat",
        exchange_manager,
        target_amount="1%",
        target_position="2"
    ) == {
        enums.TradingSignalCommonsAttrs.ACTION.value: enums.TradingSignalOrdersActions.CREATE.value,
        enums.TradingSignalOrdersAttrs.SIDE.value: enums.TradeOrderSide.BUY.value,
        enums.TradingSignalOrdersAttrs.STRATEGY.value: "strat",
        enums.TradingSignalOrdersAttrs.SYMBOL.value: "BTC/ETH",
        enums.TradingSignalOrdersAttrs.EXCHANGE.value: "binanceus",
        enums.TradingSignalOrdersAttrs.EXCHANGE_TYPE.value: enums.ExchangeTypes.SPOT.value,
        enums.TradingSignalOrdersAttrs.TYPE.value: enums.TraderOrderType.BUY_LIMIT.value,
        enums.TradingSignalOrdersAttrs.QUANTITY.value: float(buy_limit_order.origin_quantity),
        enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value: "1%",
        enums.TradingSignalOrdersAttrs.TARGET_POSITION.value: "2",
        enums.TradingSignalOrdersAttrs.UPDATED_TARGET_AMOUNT.value: None,
        enums.TradingSignalOrdersAttrs.UPDATED_TARGET_POSITION.value: None,
        enums.TradingSignalOrdersAttrs.LIMIT_PRICE.value: float(buy_limit_order.origin_price),
        enums.TradingSignalOrdersAttrs.UPDATED_LIMIT_PRICE.value: 0.0,
        enums.TradingSignalOrdersAttrs.STOP_PRICE.value: float(buy_limit_order.origin_stop_price),
        enums.TradingSignalOrdersAttrs.UPDATED_STOP_PRICE.value: 0.0,
        enums.TradingSignalOrdersAttrs.CURRENT_PRICE.value: float(buy_limit_order.created_last_price),
        enums.TradingSignalOrdersAttrs.UPDATED_CURRENT_PRICE.value: 0.0,
        enums.TradingSignalOrdersAttrs.REDUCE_ONLY.value: True,
        enums.TradingSignalOrdersAttrs.POST_ONLY.value: False,
        enums.TradingSignalOrdersAttrs.GROUP_ID.value: None,
        enums.TradingSignalOrdersAttrs.GROUP_TYPE.value: None,
        enums.TradingSignalOrdersAttrs.TAG.value: "hello",
        enums.TradingSignalOrdersAttrs.SHARED_SIGNAL_ORDER_ID.value: buy_limit_order.shared_signal_order_id,
        enums.TradingSignalOrdersAttrs.BUNDLED_WITH.value: sell_limit_order.shared_signal_order_id,
        enums.TradingSignalOrdersAttrs.CHAINED_TO.value: sell_limit_order.shared_signal_order_id,
        enums.TradingSignalOrdersAttrs.ADDITIONAL_ORDERS.value: [],
    }

    order_group = personal_data.OneCancelsTheOtherOrderGroup(
        "group_name",
        buy_limit_order.exchange_manager.exchange_personal_data.orders_manager
    )
    buy_limit_order.add_to_order_group(order_group)
    final_order_desc = {
        enums.TradingSignalCommonsAttrs.ACTION.value: enums.TradingSignalOrdersActions.CREATE.value,
        enums.TradingSignalOrdersAttrs.SIDE.value: enums.TradeOrderSide.BUY.value,
        enums.TradingSignalOrdersAttrs.STRATEGY.value: "strat",
        enums.TradingSignalOrdersAttrs.SYMBOL.value: "BTC/ETH",
        enums.TradingSignalOrdersAttrs.EXCHANGE.value: "binanceus",
        enums.TradingSignalOrdersAttrs.EXCHANGE_TYPE.value: enums.ExchangeTypes.SPOT.value,
        enums.TradingSignalOrdersAttrs.TYPE.value: enums.TraderOrderType.BUY_LIMIT.value,
        enums.TradingSignalOrdersAttrs.QUANTITY.value: float(buy_limit_order.origin_quantity),
        enums.TradingSignalOrdersAttrs.TARGET_AMOUNT.value: "10",
        enums.TradingSignalOrdersAttrs.TARGET_POSITION.value: "8%",
        enums.TradingSignalOrdersAttrs.UPDATED_TARGET_AMOUNT.value: "10",
        enums.TradingSignalOrdersAttrs.UPDATED_TARGET_POSITION.value: "8%",
        enums.TradingSignalOrdersAttrs.LIMIT_PRICE.value: 111.545445445,
        enums.TradingSignalOrdersAttrs.UPDATED_LIMIT_PRICE.value: 111.545445445,
        enums.TradingSignalOrdersAttrs.STOP_PRICE.value: 111.1,
        enums.TradingSignalOrdersAttrs.UPDATED_STOP_PRICE.value: 111.1,
        enums.TradingSignalOrdersAttrs.CURRENT_PRICE.value: 111.0,
        enums.TradingSignalOrdersAttrs.UPDATED_CURRENT_PRICE.value: 111.0,
        enums.TradingSignalOrdersAttrs.REDUCE_ONLY.value: True,
        enums.TradingSignalOrdersAttrs.POST_ONLY.value: False,
        enums.TradingSignalOrdersAttrs.GROUP_ID.value: order_group.name,
        enums.TradingSignalOrdersAttrs.GROUP_TYPE.value: personal_data.OneCancelsTheOtherOrderGroup.__name__,
        enums.TradingSignalOrdersAttrs.TAG.value: "hello",
        enums.TradingSignalOrdersAttrs.SHARED_SIGNAL_ORDER_ID.value: buy_limit_order.shared_signal_order_id,
        enums.TradingSignalOrdersAttrs.BUNDLED_WITH.value: sell_limit_order.shared_signal_order_id,
        enums.TradingSignalOrdersAttrs.CHAINED_TO.value: sell_limit_order.shared_signal_order_id,
        enums.TradingSignalOrdersAttrs.ADDITIONAL_ORDERS.value: [],
    }
    assert signals.create_order_signal_content(
        buy_limit_order,
        enums.TradingSignalOrdersActions.CREATE,
        "strat",
        exchange_manager,
        target_amount="1%",
        target_position="2",
        updated_target_amount="10",
        updated_target_position="8%",
        updated_limit_price=decimal.Decimal("111.545445445"),
        updated_stop_price=decimal.Decimal("111.1"),
        updated_current_price=decimal.Decimal("111"),
    ) == final_order_desc

    # with cleared order, gives the same signal
    buy_limit_order.clear()
    assert signals.create_order_signal_content(
        buy_limit_order,
        enums.TradingSignalOrdersActions.CREATE,
        "strat",
        exchange_manager,
        target_amount="1%",
        target_position="2",
        updated_target_amount="10",
        updated_target_position="8%",
        updated_limit_price=decimal.Decimal("111.545445445"),
        updated_stop_price=decimal.Decimal("111.1"),
        updated_current_price=decimal.Decimal("111"),
    ) == final_order_desc
