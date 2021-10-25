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

async def limit(
    trader,
    price=None,
    side=None,
    symbol=None,
    order_type="limit",
    amount=None,
    total_balance_percent=None,
    available_balance_percent=None,
    position=None,
    position_percent=None,
    amount_position_percent=None,
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
        price=price,
        tag=tag,
    )

#alias
#limitorder=limit
#limit_order=limit
#Limit_Order=limit
#limit_Order=limit
#Limit_order=limit
