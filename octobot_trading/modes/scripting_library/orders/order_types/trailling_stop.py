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


async def trailling_market(
    context,
    side=None,
    symbol=None,
    amount=None,
    target_position=None,
    min_offset=None,
    max_offset=None,
    slippage_limit=None,
    postonly=None,
    reduceonly=None,
    tag=None
) -> list:
    return await _create_order_instance(
        context.trader,
        side,
        symbol or context.traded_pair,
        amount,
        target_position=target_position,
        order_type_name="trailling_stop",
        min_offset=min_offset,
        max_offset=max_offset,
        tag=tag,
        context=context,
    )
