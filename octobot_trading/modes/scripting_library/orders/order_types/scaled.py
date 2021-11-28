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


from .create_order import _create_order_instance
from ..position_size.target_position import *
from ..offsets import *


async def scaled_limit(
        context,
        side=None,
        symbol=None,

        scale_from=None,
        scale_to=None,
        order_count=10,
        distribution="linear",

        amount=None,
        target_position=None,

        reduce_only=False,
        post_only=False,
        tag=None,
):
    amount_per_order = None
    if target_position is None and amount is not None:
        amount_per_order = amount(amount, side, symbol) / order_count  # todo round to exchange decimal and make sure total amount is same as provided

    elif target_position is not None and amount is None and side is None:
        side, total_amount = get_target_position(target_position, symbol)
        amount_per_order = total_amount / order_count  # todo round to exchange decimal and make sure total amount is same as provided
    else:
        raise RuntimeError("Either use side with amount or target_position for scaled orders.")

    scale_from_price = get_offset(scale_from)
    scale_to_price = get_offset(scale_to)
    order_price_array = []
    if distribution == "linear":
        if side == "buy":
            price_difference = scale_to_price - scale_from_price
            step_size = price_difference / order_count
            for i in range(1, order_count):
                order_price_array.append(scale_from_price + step_size)
        elif side == "sell":
            price_difference = scale_from_price - scale_to_price
            step_size = price_difference / order_count
            for i in range(1, order_count):
                order_price_array.append(scale_from_price + step_size)
        else:
            raise RuntimeError("order side is missing")

    else:
        raise RuntimeError("there is something wrong with your scaled order")

    for order in range(1, order_count):
        await _create_order_instance(
            trader=context.trader,
            side=side,
            symbol=symbol or context.symbol,

            order_amount=amount_per_order, # todo later dont double convert amount, skip check in create order for this type

            order_type_name="limit",
            order_offset=order_price_array[order],

            reduce_only=reduce_only,
            post_only=post_only,
            tag=tag,

            context=context
        )
