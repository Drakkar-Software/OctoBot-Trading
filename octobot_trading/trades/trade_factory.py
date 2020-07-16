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
from octobot_trading.data.trade import Trade
from octobot_trading.enums import OrderStatus
from octobot_trading.orders.order_factory import create_order_from_raw, create_order_from_type


def create_trade_instance_from_raw(trader, raw_trade):
    try:
        order = create_order_from_raw(trader, raw_trade)
        order.update_from_raw(raw_trade)
        if order.status is OrderStatus.CANCELED:
            order.cancel_order()
        else:
            order.consider_as_filled()
        return create_trade_from_order(order)
    except KeyError:
        # Funding trade candidate
        return None


def create_trade_from_order(order,
                            close_status=None,
                            creation_time=0,
                            canceled_time=0,
                            executed_time=0):
    if close_status is not None:
        order.status = close_status
    trade = Trade(order.trader)
    trade.update_from_order(order,
                            canceled_time=canceled_time,
                            creation_time=creation_time,
                            executed_time=executed_time)
    return trade


def create_trade_instance(trader,
                          order_type,
                          symbol,
                          status=OrderStatus.CLOSED,
                          order_id=None,
                          filled_price=0.0,
                          quantity_filled=0.0,
                          total_cost=0.0,
                          canceled_time=0,
                          creation_time=0,
                          executed_time=0):
    order = create_order_from_type(trader=trader, order_type=order_type)
    order.update(order_type=order_type,
                 symbol=symbol,
                 current_price=filled_price,
                 quantity=quantity_filled,
                 price=filled_price,
                 order_id=trader.parse_order_id(order_id),
                 filled_price=filled_price,
                 quantity_filled=quantity_filled,
                 fee=None,  # TODO
                 total_cost=total_cost)
    return create_trade_from_order(order,
                                   close_status=status,
                                   canceled_time=canceled_time,
                                   creation_time=creation_time,
                                   executed_time=executed_time)
