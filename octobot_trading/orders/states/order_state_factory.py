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
from octobot_trading.enums import OrderStatus


async def create_order_state(order, is_from_exchange_data=False):
    if order.status is OrderStatus.OPEN:
        await order.on_open(force_open=True, is_from_exchange_data=is_from_exchange_data)
    elif order.status in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED]:
        await order.on_fill(force_fill=True, is_from_exchange_data=is_from_exchange_data)
    elif order.status is OrderStatus.CANCELED:
        await order.on_cancel(force_cancel=True, is_from_exchange_data=is_from_exchange_data)
    elif order.status is OrderStatus.CLOSED:
        await order.on_close(force_close=True, is_from_exchange_data=is_from_exchange_data)
