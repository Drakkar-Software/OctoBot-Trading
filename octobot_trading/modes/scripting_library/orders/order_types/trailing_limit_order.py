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

import octobot_trading.modes.scripting_library.orders.order_types.create_order as create_order


async def trailing_limit(
    context,
    side=None,
    symbol=None,

    amount=None,
    target_position=None,

    offset=None,
    min_offset=None,
    max_offset=None,

    slippage_limit=None,
    time_limit=None,

    reduce_only=False,
    post_only=False,
    one_cancels_the_other=False,

    tag=None,

    linked_to=None
):
    return await create_order.create_order_instance(
        context,
        side=side,
        symbol=symbol or context.symbol,

        order_amount=amount,
        order_target_position=target_position,

        order_type_name="trailing_limit",

        order_min_offset=min_offset,
        order_max_offset=max_offset,
        order_offset=offset,

        slippage_limit=slippage_limit,
        time_limit=time_limit,
        reduce_only=reduce_only,
        post_only=post_only,
        one_cancels_the_other=one_cancels_the_other,

        tag=tag,

        linked_to=linked_to
    )
