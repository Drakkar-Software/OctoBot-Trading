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
import octobot_trading.personal_data as personal_data
import octobot_trading.enums as enums
import octobot_trading.constants as constants


def create_order_from_raw(trader, raw_order):
    _, order_type = personal_data.parse_order_type(raw_order)
    return create_order_from_type(trader, order_type)


def create_order_instance_from_raw(trader, raw_order, force_open=False):
    order = create_order_from_raw(trader, raw_order)
    order.update_from_raw(raw_order)
    if force_open:
        order.status = enums.OrderStatus.OPEN
    return order


def create_order_from_type(trader, order_type, side=None):
    if side is None:
        return personal_data.TraderOrderTypeClasses[order_type](trader)
    return personal_data.TraderOrderTypeClasses[order_type](trader, side=side)


def create_order_instance(trader,
                          order_type,
                          symbol,
                          current_price,
                          quantity,
                          price=constants.ZERO,
                          stop_price=constants.ZERO,
                          status=enums.OrderStatus.OPEN,
                          order_id=None,
                          filled_price=constants.ZERO,
                          average_price=constants.ZERO,
                          quantity_filled=constants.ZERO,
                          total_cost=constants.ZERO,
                          timestamp=0,
                          side=None,
                          fees_currency_side=None,
                          group=None,
                          tag=None,
                          reduce_only=None,
                          quantity_currency=None):
    order = create_order_from_type(trader=trader,
                                   order_type=order_type,
                                   side=side)
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
                 average_price=average_price,
                 quantity_filled=quantity_filled,
                 fee=None,
                 total_cost=total_cost,
                 fees_currency_side=fees_currency_side,
                 group=group,
                 tag=tag,
                 reduce_only=reduce_only,
                 quantity_currency=quantity_currency)
    order.ensure_order_id()
    return order
