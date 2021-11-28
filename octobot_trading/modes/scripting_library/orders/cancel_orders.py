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

from .order_tags import *


async def cancel_orders(ctx, which="all") -> bool:
    order_ids = None
    orders_canceled = False
    if which == "all":
        order_ids = ctx
    elif which == "sell":
        order_ids = ctx
    elif which == "buy":
        order_ids = ctx
    else:  # tagged order
        order_ids = get_tagged_orders(ctx, which)
    for order_id in order_ids:
        if await ctx.exchange_manager.trader.cancel_order(
                ctx.exchange_manager.exchange_personal_data.orders_manager.get_order(
                    order_id
                )
        ):
            ctx.logger.info(f"Order canceled on {ctx.exchange_manager.exchange_name} for {ctx.symbol}")
            orders_canceled = True
    return orders_canceled
