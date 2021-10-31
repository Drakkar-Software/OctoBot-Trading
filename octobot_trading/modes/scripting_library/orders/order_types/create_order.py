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
from .. import position_size


async def _create_order_instance(
    trader,
    side=None,
    symbol=None,

    # todo simplify amount into amount="1%" or "100%p" or "1000" or "50%a"
    amount=None,
    target_position=None,

    order_type_name=None,
    price=None,


    offset=None,
    min_offset=None,
    max_offset=None,


    reduce_only=False,    #Todo
    post_only=False,    #Todo
    tag=None,    #Todo

    context=None
):
    # 1. create order instance
    current_symbol_holding, current_market_holding, market_quantity, current_price, symbol_market = \
        await trading_personal_data.get_pre_order_data(trader.exchange_manager,
                                                       symbol=symbol,
                                                       timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT)
    order_quantity = None
    order_type = None

    # size based on amount
    if side is not None:

        if amount is not None:
            order_quantity = position_size.amount(amount, side, current_symbol_holding, market_quantity)

        if order_quantity is None:
            raise RuntimeError("No provided quantity to create order.")
        if order_quantity == 0:
            raise RuntimeError("Computed quantity for order is 0.")
        if side != "buy" and side != "sell":
            raise RuntimeError("Side parameter needs to be buy or sell.")

    #size and side based on target position
    if side is None:
        if order_quantity is None and target_position is not None:
            raise RuntimeError("Either use side with amount or target_position.")

        if target_position is not None:
            order_quantity = position_size.target_position(target_position)
            side = position_size.target_position_side(order_quantity)
            if order_quantity is None:
                raise RuntimeError("No provided quantity to create order.")
            if order_quantity == 0:
                raise RuntimeError("Computed quantity for order is 0.")


    # order types
    #normal order
    side = None
    if order_type_name == "market":
        order_type = trading_enums.TraderOrderType.SELL_MARKET if side == "sell" else trading_enums.TraderOrderType.BUY_MARKET

    if order_type_name == "limit":
        order_type = trading_enums.TraderOrderType.SELL_LIMIT if side == "sell" else trading_enums.TraderOrderType.BUY_LIMIT
    if offset is not None and min_offset:
    # conditional orders
        # should be a real SL on the exchange short and long
        if order_type_name == "stop_loss":
            order_type = None # todo
        # should be conditional order on the exchange
        if order_type_name == "stop_market":
            order_type = None # todo
        # has a trigger price and a offset where the limit gets placed when triggered - conditional order on exchange possible?
        if order_type_name == "stop_limit":
            order_type = None # todo

    # trailling orders
    if order_type_name == "trailling_stop_loss":
        # should be a real trailling on the exchange - short and long
        # TODO
        pass
    if order_type_name == "trailling_stop":
        order_type = trading_enums.TraderOrderType.TRAILING_STOP
        side = trading_enums.TradeOrderSide.SELL if side == "sell" else trading_enums.TradeOrderSide.BUY
    if order_type_name == "trailling_limit":
        order_type = trading_enums.TraderOrderType.SELL_LIMIT if side == "sell" else trading_enums.TraderOrderType.BUY_LIMIT
        side = trading_enums.TradeOrderSide.SELL if side == "sell" else trading_enums.TradeOrderSide.BUY

    if min_offset is not None and max_offset is None:
        # TODO
        pass

    orders = []
    for order_quantity, order_price in trading_personal_data.decimal_check_and_adapt_order_details_if_necessary(
            order_quantity,
            price if price else current_price,
            symbol_market):
        created_order = trading_personal_data.create_order_instance(
            trader=trader,
            order_type=order_type,
            symbol=symbol,
            current_price=current_price,
            quantity=order_quantity,
            price=price,
            side=side)
        if min_offset is not None:
            await created_order.set_trailing_percent(min_offset)
        # 2. submit it to trader
        created_order = await trader.create_order(created_order)
        orders.append(created_order)
    if context is not None:
        library_data.store_orders(context, orders)
    return orders


