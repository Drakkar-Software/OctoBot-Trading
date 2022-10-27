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

from octobot_trading.personal_data.orders import order_state
from octobot_trading.personal_data.orders.order_state import (
    OrderState,
)
from octobot_trading.personal_data.orders import order_group
from octobot_trading.personal_data.orders.order_group import (
    OrderGroup,
)
from octobot_trading.personal_data.orders import groups
from octobot_trading.personal_data.orders.groups import (
    BalancedTakeProfitAndStopOrderGroup,
    OneCancelsTheOtherOrderGroup,
)
from octobot_trading.personal_data.orders import order
from octobot_trading.personal_data.orders.order import (
    Order,
    parse_order_type,
)
from octobot_trading.personal_data.orders import types
from octobot_trading.personal_data.orders.types import (
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
from octobot_trading.personal_data.orders import states
from octobot_trading.personal_data.orders.states import (
    CloseOrderState,
    CancelOrderState,
    OpenOrderState,
    create_order_state,
    FillOrderState,
    PendingCreationOrderState,
)
from octobot_trading.personal_data.orders import channel
from octobot_trading.personal_data.orders.channel import (
    OrdersProducer,
    OrdersChannel,
    OrdersUpdater,
    OrdersUpdaterSimulator,
)
from octobot_trading.personal_data.orders import orders_manager
from octobot_trading.personal_data.orders.orders_manager import (
    OrdersManager,
)
from octobot_trading.personal_data.orders import order_util
from octobot_trading.personal_data.orders.order_util import (
    is_valid,
    get_min_max_amounts,
    check_cost,
    get_futures_max_order_size,
    get_max_order_quantity_for_price,
    total_fees_from_order_dict,
    get_fees_for_currency,
    parse_raw_fees,
    parse_order_status,
    parse_is_cancelled,
    get_up_to_date_price,
    get_pre_order_data,
    get_pnl_transaction_source_from_order,
    is_stop_order,
    create_as_chained_order,
    is_associated_pending_order,
    apply_pending_order_from_created_order,
    ensure_orders_relevancy,
    get_order_quantity_currency,
    get_order_size_portfolio_percent,
    generate_order_id,
)
from octobot_trading.personal_data.orders import order_adapter
from octobot_trading.personal_data.orders.order_adapter import (
    adapt_price,
    adapt_quantity,
    trunc_with_n_decimal_digits,
    adapt_order_quantity_because_quantity,
    adapt_order_quantity_because_price,
    split_orders,
    check_and_adapt_order_details_if_necessary,
    add_dusts_to_quantity_if_necessary,
)
from octobot_trading.personal_data.orders.decimal_order_adapter import (
    get_minimal_order_amount,
    decimal_adapt_price,
    decimal_adapt_quantity,
    decimal_trunc_with_n_decimal_digits,
    decimal_adapt_order_quantity_because_quantity,
    decimal_adapt_order_quantity_because_price,
    decimal_split_orders,
    decimal_check_and_adapt_order_details_if_necessary,
    decimal_add_dusts_to_quantity_if_necessary,
)
from octobot_trading.personal_data.orders import order_factory
from octobot_trading.personal_data.orders.order_factory import (
    create_order_from_raw,
    create_order_instance_from_raw,
    create_order_from_type,
    create_order_instance,
)

__all__ = [
    "Order",
    "parse_order_type",
    "is_valid",
    "get_min_max_amounts",
    "check_cost",
    "get_futures_max_order_size",
    "get_max_order_quantity_for_price",
    "total_fees_from_order_dict",
    "get_fees_for_currency",
    "parse_raw_fees",
    "parse_order_status",
    "parse_is_cancelled",
    "get_up_to_date_price",
    "get_pre_order_data",
    "get_pnl_transaction_source_from_order",
    "create_as_chained_order",
    "ensure_orders_relevancy",
    "get_order_quantity_currency",
    "get_order_size_portfolio_percent",
    "generate_order_id",
    "is_associated_pending_order",
    "apply_pending_order_from_created_order",
    "OrderState",
    "OrderGroup",
    "BalancedTakeProfitAndStopOrderGroup",
    "OneCancelsTheOtherOrderGroup",
    "OrdersUpdater",
    "adapt_price",
    "get_minimal_order_amount",
    "decimal_adapt_price",
    "adapt_quantity",
    "decimal_adapt_quantity",
    "trunc_with_n_decimal_digits",
    "decimal_trunc_with_n_decimal_digits",
    "adapt_order_quantity_because_quantity",
    "decimal_adapt_order_quantity_because_quantity",
    "adapt_order_quantity_because_price",
    "decimal_adapt_order_quantity_because_price",
    "split_orders",
    "decimal_split_orders",
    "check_and_adapt_order_details_if_necessary",
    "decimal_check_and_adapt_order_details_if_necessary",
    "add_dusts_to_quantity_if_necessary",
    "decimal_add_dusts_to_quantity_if_necessary",
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
    "create_order_state",
    "FillOrderState",
    "PendingCreationOrderState",
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
