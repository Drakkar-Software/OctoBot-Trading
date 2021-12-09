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

import octobot_trading.enums as trading_enums
import octobot_trading.errors as trading_errors
import octobot_trading.modes.scripting_library.dsl as dsl
import octobot_trading.modes.scripting_library.data.reading.exchange_private_data as exchange_private_data
import octobot_trading.modes.scripting_library.orders.open_orders as open_orders


async def get_target_position(
        context=None,
        target=None
):
    # If an order is already open on this position, do not accept target position parameters
    # as they would interfere with the previous order target position
    if open_orders.get_open_orders(context):
        raise trading_errors.ConflictingOrdersError(
            f"Impossible to set a new target position when a related order is already in open. "
            f"Cancel other {context.symbol} order(s) first.")
    target_position_type, target_position_value = dsl.parse_quantity(target)

    if target_position_type is dsl.QuantityType.POSITION_PERCENT:
        open_position_size_val = exchange_private_data.open_position_size(context)
        target_size = open_position_size_val * target_position_value / 100
        order_size = target_size - open_position_size_val

    elif target_position_type is dsl.QuantityType.PERCENT:
        total_acc_bal = await exchange_private_data.total_account_balance(context)
        target_size = total_acc_bal * target_position_value / 100
        order_size = target_size - exchange_private_data.open_position_size(context)

    # in target position, we always provide the position size we want to end up with
    elif target_position_type is dsl.QuantityType.DELTA or target_position_type is dsl.QuantityType.FLAT:
        order_size = target_position_value - exchange_private_data.open_position_size(context)

    elif target_position_type is dsl.QuantityType.AVAILABLE_PERCENT:
        available_account_balance_val = await exchange_private_data.available_account_balance(context)
        order_size = available_account_balance_val * target_position_value / 100

    else:
        raise trading_errors.InvalidArgumentError("make sure to use a supported syntax for position")

    side = get_target_position_side(order_size)
    if side == trading_enums.TradeOrderSide.SELL.value:
        order_size = order_size * -1

    order_size = await exchange_private_data.adapt_amount_to_holdings(context, order_size, side)
    return order_size, side


def get_target_position_side(order_size):
    if order_size < 0:
        return trading_enums.TradeOrderSide.SELL.value
    elif order_size > 0:
        return trading_enums.TradeOrderSide.BUY.value
    # order_size == 0
    raise RuntimeError("Computed position size is 0")
