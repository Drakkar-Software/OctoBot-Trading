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

from octobot_trading.personal_data.orders cimport order_state
from octobot_trading.personal_data.orders.order_state cimport (
    OrderState,
)
from octobot_trading.personal_data.orders cimport order
from octobot_trading.personal_data.orders.order cimport (
    Order,
)

from octobot_trading.personal_data.orders cimport orders_manager
from octobot_trading.personal_data.orders.orders_manager cimport (
    OrdersManager,
)

from octobot_trading.personal_data.orders cimport order_util
from octobot_trading.personal_data.orders cimport order_adapter
from octobot_trading.personal_data.orders cimport order_factory
from octobot_trading.personal_data.orders cimport types
from octobot_trading.personal_data.orders.types cimport (
    UnknownOrder,
    MarketOrder,
    SellMarketOrder,
    BuyMarketOrder,
    BuyLimitOrder,
    SellLimitOrder,
    LimitOrder,
    TakeProfitOrder,
    StopLossOrder,
    StopLossLimitOrder,
    TakeProfitLimitOrder,
    TrailingStopOrder,
    TrailingStopLimitOrder,
)

from octobot_trading.personal_data.orders cimport states
from octobot_trading.personal_data.orders.states cimport (
    CloseOrderState,
    CancelOrderState,
    OpenOrderState,
    FillOrderState,
)

from octobot_trading.personal_data.orders cimport channel
from octobot_trading.personal_data.orders.channel cimport (
    OrdersProducer,
    OrdersChannel,
    OrdersUpdater,
    OrdersUpdaterSimulator,
)

from octobot_trading.personal_data.orders.order_util cimport (
    is_valid,
    get_min_max_amounts,
    check_cost,
    total_fees_from_order_dict,
    get_fees_for_currency,
    parse_raw_fees,
    parse_order_status,
    parse_is_cancelled,
)
from octobot_trading.personal_data.orders.order_adapter cimport (
    adapt_price,
    adapt_quantity,
    adapt_order_quantity_because_quantity,
    adapt_order_quantity_because_price,
    split_orders,
    check_and_adapt_order_details_if_necessary,
    add_dusts_to_quantity_if_necessary,
)
from octobot_trading.personal_data.orders.order_factory cimport (
    create_order_from_raw,
    create_order_instance_from_raw,
    create_order_from_type,
    create_order_instance,
)

__all__ = [
    "Order",
    "is_valid",
    "get_min_max_amounts",
    "check_cost",
    "total_fees_from_order_dict",
    "get_fees_for_currency",
    "parse_raw_fees",
    "parse_order_status",
    "parse_is_cancelled",
    "OrderState",
    "OrdersUpdater",
    "adapt_price",
    "adapt_quantity",
    "adapt_order_quantity_because_quantity",
    "adapt_order_quantity_because_price",
    "split_orders",
    "check_and_adapt_order_details_if_necessary",
    "add_dusts_to_quantity_if_necessary",
    "create_order_from_raw",
    "create_order_instance_from_raw",
    "create_order_from_type",
    "create_order_instance",
    "OrdersProducer",
    "OrdersChannel",
    "OrdersManager",
    "OrdersUpdaterSimulator",
    "CloseOrderState",
    "CancelOrderState",
    "OpenOrderState",
    "FillOrderState",
    "UnknownOrder",
    "MarketOrder",
    "SellMarketOrder",
    "BuyMarketOrder",
    "BuyLimitOrder",
    "SellLimitOrder",
    "LimitOrder",
    "TakeProfitOrder",
    "StopLossOrder",
    "StopLossLimitOrder",
    "TakeProfitLimitOrder",
    "TrailingStopOrder",
    "TrailingStopLimitOrder",
]
