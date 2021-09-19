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
import octobot_commons.logging as logging
import octobot_trading.personal_data.trades.trade as trade_class
import octobot_trading.personal_data.orders.order_factory as order_factory
import octobot_trading.enums as enums
import octobot_trading.constants as constants


def create_trade_instance_from_raw(trader, raw_trade):
    try:
        order = order_factory.create_order_from_raw(trader, raw_trade)
        order.update_from_raw(raw_trade)
        if order.status is enums.OrderStatus.CANCELED:
            # ensure order is considered canceled
            order.consider_as_canceled()
        else:
            # ensure order is considered filled
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
    trade = trade_class.Trade(order.trader)
    trade.update_from_order(order,
                            canceled_time=canceled_time,
                            creation_time=creation_time,
                            executed_time=executed_time)
    if trade.get_time() < constants.MINIMUM_VAL_TRADE_TIME:
        logging.get_logger("TradeFactory").error(f"Trade with invalid trade time ({trade.get_time()}) "
                                                 f"from order: {order}")
    return trade


def create_trade_instance(trader,
                          order_type,
                          symbol,
                          status=enums.OrderStatus.CLOSED,
                          order_id=None,
                          filled_price=constants.ZERO,
                          quantity_filled=constants.ZERO,
                          total_cost=constants.ZERO,
                          canceled_time=0,
                          creation_time=0,
                          executed_time=0):
    order = order_factory.create_order_from_type(trader=trader, order_type=order_type)
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
