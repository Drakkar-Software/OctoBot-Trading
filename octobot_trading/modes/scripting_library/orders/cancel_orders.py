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

import octobot_trading.modes.scripting_library.orders.order_tags as order_tags
import octobot_trading.enums as enums


async def cancel_orders(ctx, which="all", symbol=None, symbols=None, cancel_loaded_orders=True) -> bool:
    symbols = symbols or [symbol] if symbol else [ctx.symbol]
    order_ids = None
    orders_canceled = False
    side = None
    if which == "all":
        side = None
    elif which == "sell":
        side = enums.TradeOrderSide.SELL
    elif which == "buy":
        side = enums.TradeOrderSide.BUY
    else:  # tagged order
        order_ids = order_tags.get_tagged_orders(ctx, which)
    if order_ids:
        for order_id in order_ids:
            await ctx.exchange_manager.trader.cancel_order
            if await ctx.exchange_manager.trader.cancel_order_with_id(order_id):
                orders_canceled = True
    for symbol in symbols:
        await ctx.trader.cancel_open_orders(symbol, cancel_loaded_orders=cancel_loaded_orders, side=side)
        orders_canceled = True
    return orders_canceled
