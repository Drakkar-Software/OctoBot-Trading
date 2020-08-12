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
from octobot_trading.enums import OrderStatus, OrderStates


async def create_order_state(order, is_from_exchange_data=False, ignore_states=None):
    if ignore_states is None:
        ignore_states = []

    if order.status is OrderStatus.OPEN and OrderStates.OPEN not in ignore_states:
        await order.on_open(force_open=True, is_from_exchange_data=is_from_exchange_data)
    elif order.status in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED] and OrderStates.FILLED not in ignore_states:
        await order.on_fill(force_fill=True, is_from_exchange_data=is_from_exchange_data)
    elif order.status is OrderStatus.CANCELED and OrderStates.CANCELED not in ignore_states:
        await order.on_cancel(force_cancel=True, is_from_exchange_data=is_from_exchange_data)
    elif order.status is OrderStatus.CLOSED and OrderStates.CLOSED not in ignore_states:
        await order.on_close(force_close=True, is_from_exchange_data=is_from_exchange_data)
