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

import octobot_trading.personal_data as trading_personal_data
import octobot_trading.constants as trading_constants
import octobot_trading.enums as trading_enums
import octobot_trading.modes.scripting_library.data as library_data
import octobot_trading.modes.scripting_library.orders.position_size as position_size
import octobot_trading.modes.scripting_library.orders.offsets as offsets


async def create_order_instance(
        context,
        side=None,
        symbol=None,

        order_amount=None,
        order_target_position=None,

        order_type_name=None,

        order_offset=None,
        order_min_offset=None,
        order_max_offset=None,
        order_limit_offset=None,  # todo

        slippage_limit=None,
        time_limit=None,

        reduce_only=False,  # Todo
        post_only=False,  # Todo
        tag=None,  # Todo
):
    order_quantity, side = await _get_order_quantity_and_side(context, order_amount, order_target_position,
                                                              order_type_name, side)

    order_type, order_price, side, reduce_only, trailing_method, \
    min_offset_val, max_offset_val, order_limit_offset, limit_offset_val = \
        await _get_order_details(context, order_type_name, side, order_offset, reduce_only, order_limit_offset)

    return await _create_order(context, symbol, order_quantity, order_price,
                               order_type, side, order_min_offset, max_offset_val)


async def _get_order_quantity_and_side(context, order_amount, order_target_position, order_type_name, side):
    if order_amount is not None and order_target_position is not None:
        raise RuntimeError("order_amount and order_target_position can't be both given as parameter")

    # size based on amount
    if side is not None and order_amount is not None:
        # side
        if side != trading_enums.TradeOrderSide.BUY.value and side != trading_enums.TradeOrderSide.SELL.value:
            # we should skip that cause of performance
            raise RuntimeError(f"Side parameter needs to be {trading_enums.TradeOrderSide.BUY.value} "
                               f"or {trading_enums.TradeOrderSide.SELL.value} for your {order_type_name}.")
        return await position_size.get_amount(context, order_amount, side), side

    # size and side based on target position
    if order_target_position is not None:
        return await position_size.get_target_position(context, order_target_position)

    raise RuntimeError("Either use side with amount or target_position.")


async def _get_order_details(context, order_type_name, side, order_offset, reduce_only, order_limit_offset):
    # order types
    order_type = None

    order_price = None
    min_offset_val = None
    max_offset_val = None
    limit_offset_val = None
    trailing_method = None

    # normal order
    if order_type_name == "market":
        order_type = trading_enums.TraderOrderType.SELL_MARKET if side == trading_enums.TradeOrderSide.SELL.value \
            else trading_enums.TraderOrderType.BUY_MARKET
        order_price = await offsets.get_offset(context, "0")
        side = None

    elif order_type_name == "limit":
        order_type = trading_enums.TraderOrderType.SELL_LIMIT if side == trading_enums.TradeOrderSide.SELL.value \
            else trading_enums.TraderOrderType.BUY_LIMIT
        order_price = await offsets.get_offset(context, order_offset)
        side = None
        # todo post only

    # conditional orders
    # should be a real SL on the exchange short and long
    elif order_type_name == "stop_loss":
        order_type = trading_enums.TraderOrderType.STOP_LOSS
        side = trading_enums.TradeOrderSide.SELL if side == trading_enums.TradeOrderSide.SELL.value \
            else trading_enums.TradeOrderSide.BUY
        order_price = await offsets.get_offset(context, order_offset)
        reduce_only = True

    # should be conditional order on the exchange
    elif order_type_name == "stop_market":
        order_type = None  # todo
        order_price = await offsets.get_offset(context, order_offset)

    # has a trigger price and a offset where the limit gets placed when triggered -
    # conditional order on exchange possible?
    elif order_type_name == "stop_limit":
        order_type = None  # todo
        order_price = await offsets.get_offset(context, order_offset)
        order_limit_offset = await offsets.get_offset(context, order_offset)
        # todo post only

    # trailling orders
    # should be a real trailing stop loss on the exchange - short and long
    elif order_type_name == "trailing_stop_loss":
        order_price = await offsets.get_offset(context, order_offset)
        order_type = None  # todo
        reduce_only = True
        trailing_method = "continuous"
        # todo make sure order gets replaced by market if price jumped below price before order creation

    # todo should use trailing on exchange if available or replace order on exchange
    elif order_type_name == "trailing_market":
        order_price = await offsets.get_offset(context, order_offset)
        trailing_method = "continuous"
        order_type = trading_enums.TraderOrderType.TRAILING_STOP
        side = trading_enums.TradeOrderSide.SELL if side == trading_enums.TradeOrderSide.SELL.value \
            else trading_enums.TradeOrderSide.BUY

    # todo should use trailing on exchange if available or replace order on exchange
    elif order_type_name == "trailing_limit":
        order_type = trading_enums.TraderOrderType.TRAILING_STOP_LIMIT
        side = trading_enums.TradeOrderSide.SELL if side == trading_enums.TradeOrderSide.SELL.value \
            else trading_enums.TradeOrderSide.BUY
        trailing_method = "continuous"
        min_offset_val = await offsets.get_offset(context, order_offset)
        # todo If the price changes such that the order becomes more than maxOffset away from the
        #  price, then the order will be moved to minOffset away again.
        max_offset_val = await offsets.get_offset(context, order_offset)
        # todo post only

    return order_type, order_price, side, reduce_only, trailing_method, \
           min_offset_val, max_offset_val, order_limit_offset, limit_offset_val


async def _create_order(context, symbol, order_quantity, order_price,
                        order_type, side, order_min_offset, max_offset_val):
    # todo handle offsets, reduce_only, post_only,
    _, _, _, current_price, symbol_market = \
        await trading_personal_data.get_pre_order_data(context.exchange_manager,
                                                       symbol=symbol,
                                                       timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT)
    orders = []
    for final_order_quantity, final_order_price in \
            trading_personal_data.decimal_check_and_adapt_order_details_if_necessary(
                order_quantity,
                order_price,
                symbol_market
            ):
        created_order = trading_personal_data.create_order_instance(
            trader=context.trader,
            order_type=order_type,
            symbol=symbol,
            current_price=current_price,
            quantity=final_order_quantity,
            price=final_order_price,
            side=side
        )
        if order_min_offset is not None:
            await created_order.set_trailing_percent(order_min_offset)
        # 2. submit it to trader
        created_order = await context.trader.create_order(created_order)
        orders.append(created_order)
    if context is not None:
        await library_data.store_orders(context, orders)
    return orders
