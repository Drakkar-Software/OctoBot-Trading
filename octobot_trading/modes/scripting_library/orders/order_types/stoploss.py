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


async def stop(
    trader,
    side=None,
    symbol=None,
    order_type="stop",
    amount=None,
    total_balance_percent=None,
    available_balance_percent=None,
    position=None,
    position_percent=None,
    amount_position_percent=None,

    reduceonly=True,
    postonly=False,
    min_offset_percent=None,
    max_offset_percent=None,
    slippage_limit=None,
    post_only=False,
    tag=None,
):
    await _create_order_instance(
        trader,
        side,
        symbol,
        amount,
        total_balance_percent=total_balance_percent,
        available_balance_percent=available_balance_percent,
        position=position,
        position_percent=position_percent,
        amount_position_percent=amount_position_percent,
        order_type=order_type,
        min_offset_percent=min_offset_percent,
        max_offset_percent=max_offset_percent,
        tag=tag,
        reduceonly=reduceonly
    )
