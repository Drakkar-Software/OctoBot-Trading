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
from octobot_trading.data.order import parse_order_type, Order
from octobot_trading.enums import OrderStatus
from octobot_trading.orders.types import TraderOrderTypeClasses


def create_order_from_raw(trader, raw_order):
    _, order_type = parse_order_type(raw_order)
    return create_order_from_type(trader, order_type)


def create_order_instance_from_raw(trader, raw_order):
    order = create_order_from_raw(trader, raw_order)
    order.update_from_raw(raw_order)
    return order


def create_order_from_type(trader, order_type):
    return TraderOrderTypeClasses[order_type](trader) if order_type is not None else Order(trader)


def create_order_instance(trader,
                          order_type,
                          symbol,
                          current_price,
                          quantity,
                          price=0.0,
                          stop_price=0.0,
                          linked_to=None,
                          status=OrderStatus.OPEN,
                          order_id=None,
                          filled_price=0.0,
                          quantity_filled=0.0,
                          total_cost=0.0,
                          timestamp=0,
                          linked_portfolio=None):
    order = create_order_from_type(trader=trader,
                                   order_type=order_type)
    order.update(order_type=order_type,
                 symbol=symbol,
                 current_price=current_price,
                 quantity=quantity,
                 price=price,
                 stop_price=stop_price,
                 order_id=trader.parse_order_id(order_id),
                 timestamp=timestamp,
                 status=status,
                 filled_price=filled_price,
                 quantity_filled=quantity_filled,
                 fee=None,
                 total_cost=total_cost,
                 linked_to=linked_to,
                 linked_portfolio=linked_portfolio)

    return order
