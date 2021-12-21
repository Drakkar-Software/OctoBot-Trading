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
import asyncio

import octobot_trading.personal_data as trading_personal_data
import octobot_trading.constants as trading_constants
import octobot_trading.enums as trading_enums
import octobot_trading.errors as trading_errors
import octobot_trading.modes.scripting_library.data as library_data
import octobot_trading.modes.scripting_library.orders.position_size as position_size
import octobot_trading.modes.scripting_library.orders.offsets as offsets
import octobot_trading.modes.scripting_library.orders.order_tags as order_tags


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
    one_cancels_the_other=False,
    tag=None,

    linked_to=None
):
    if _paired_order_is_closed(context, linked_to, one_cancels_the_other, tag):
        return []
    async with context.exchange_manager.exchange_personal_data.portfolio_manager.portfolio.lock:
        order_quantity, side = await _get_order_quantity_and_side(context, order_amount, order_target_position,
                                                                  order_type_name, side, reduce_only)

        order_type, order_price, side, reduce_only, trailing_method, \
        min_offset_val, max_offset_val, order_limit_offset, limit_offset_val = \
            await _get_order_details(context, order_type_name, side, order_offset, reduce_only, order_limit_offset)

        return await _create_order(context, symbol, order_quantity, order_price, tag,
                                   order_type, side, order_min_offset, max_offset_val,
                                   linked_to, one_cancels_the_other)


def _paired_order_is_closed(context, linked_to, one_cancels_the_other, tag):
    if linked_to is not None and linked_to.is_closed():
        return True
    if one_cancels_the_other:
        for order in context.just_created_orders:
            if order.one_cancels_the_other and order.tag == tag and order.is_closed():
                return True
    return False


def _use_total_holding(order_type_name):
    return _is_stop_order(order_type_name)


def _is_stop_order(order_type_name):
    return "stop" in order_type_name


async def _get_order_quantity_and_side(context, order_amount, order_target_position,
                                       order_type_name, side, reduce_only):
    if order_amount is not None and order_target_position is not None:
        raise trading_errors.InvalidArgumentError("order_amount and order_target_position can't be "
                                                  "both given as parameter")

    use_total_holding = _use_total_holding(order_type_name)
    is_stop_order = _is_stop_order(order_type_name)
    # size based on amount
    if side is not None and order_amount is not None:
        # side
        if side != trading_enums.TradeOrderSide.BUY.value and side != trading_enums.TradeOrderSide.SELL.value:
            # we should skip that cause of performance
            raise trading_errors.InvalidArgumentError(
                f"Side parameter needs to be {trading_enums.TradeOrderSide.BUY.value} "
                f"or {trading_enums.TradeOrderSide.SELL.value} for your {order_type_name}.")
        return await position_size.get_amount(context, order_amount, side, reduce_only, is_stop_order,
                                              use_total_holding=use_total_holding), side

    # size and side based on target position
    if order_target_position is not None:
        return await position_size.get_target_position(context, order_target_position, reduce_only, is_stop_order,
                                                       use_total_holding=use_total_holding)

    raise trading_errors.InvalidArgumentError("Either use side with amount or target_position.")


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


async def _create_order(context, symbol, order_quantity, order_price, tag, order_type, side,
                        order_min_offset, max_offset_val, linked_to, one_cancels_the_other):
    # todo handle offsets, reduce_only, post_only,
    orders = []
    error_message = ""
    if isinstance(linked_to, list) and linked_to:
        linked_to = linked_to[0]
    elif isinstance(linked_to, trading_personal_data.Order):
        linked_to = linked_to
    else:
        linked_to = None
    try:
        _, _, _, current_price, symbol_market = \
            await trading_personal_data.get_pre_order_data(context.exchange_manager,
                                                           symbol=symbol,
                                                           timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT)
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
                side=side,
                allow_self_managed=context.allow_self_managed_orders,
                linked_to=linked_to,
                one_cancels_the_other=one_cancels_the_other,
                tag=tag
            )
            if order_min_offset is not None:
                await created_order.set_trailing_percent(order_min_offset)
            pre_init_callback = _pre_initialize_order_callback if linked_to is None and one_cancels_the_other else None
            created_order = await context.trader.create_order(created_order, pre_init_callback=pre_init_callback)
            context.just_created_orders.append(created_order)
            orders.append(created_order)
    except (trading_errors.MissingFunds, trading_errors.MissingMinimalExchangeTradeVolume):
        error_message = "missing minimal funds"
    except asyncio.TimeoutError as e:
        error_message = f"{e} and is necessary to compute the order details"
    except Exception as e:
        error_message = f"failed to create order : {e}."
        context.logger.exception(e, True, f"Failed to create order : {e}.")
    if orders:
        if context is not None and context.plot_orders:
            await library_data.store_orders(context, orders)
    else:
        error_message = f"not enough funds"
    if error_message:
        context.logger.warning(f"No order created when asking for {symbol} {order_type} "
                               f"with a volume of {order_quantity} on {context.exchange_manager.exchange_name}: "
                               f"{error_message}.")
    return orders


async def _pre_initialize_order_callback(created_order):
    # cancel all other orders with same symbol and one_cancels_the_other,
    # filter by tag if provided
    for order in created_order.trader.exchange_manager.exchange_personal_data.orders_manager.get_open_orders(
       symbol=created_order.symbol,
       tag=created_order.tag):
        if created_order is not order and order.one_cancels_the_other:
            order.add_linked_order(created_order)
            created_order.add_linked_order(order)
