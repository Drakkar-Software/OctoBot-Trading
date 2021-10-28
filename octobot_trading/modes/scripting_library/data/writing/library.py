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


def log_orders(writer, orders):
    order_data = [
        {
            "time": order.creation_time,
            "type": order.order_type.name if order.order_type is not None else 'Unknown',
            "volume": float(order.origin_quantity),
            "price": float(order.origin_price),
            "state": order.state.state.value if order.state is not None else 'Unknown',
        }
        for order in orders
    ]
    writer.log_many("orders", order_data)
