# cython: language_level=3
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
#  Lesser General License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.


""" Order class will represent an open order in the specified exchange
In simulation it will also define rules to be filled / canceled
It is also use to store creation & fill values of the order """
from octobot_trading.orders.order_state cimport OrderState
from octobot_trading.util.initializable cimport Initializable

from octobot_trading.data.portfolio cimport Portfolio

cdef class Order(Initializable):
    cdef public object trader
    cdef public object exchange_manager

    cdef public object side # TradeOrderSide
    cdef public object status # OrderStatus
    cdef public object order_type # TraderOrderType
    cdef public object lock # Lock

    cdef public Order linked_to
    cdef public Portfolio linked_portfolio
    cdef public OrderState state

    cdef public bint is_simulated
    cdef public bint is_synchronized_with_exchange
    cdef public bint is_from_this_octobot
    cdef public bint simulated

    cdef public str symbol
    cdef public str currency
    cdef public str market
    cdef public str taker_or_maker
    cdef public str order_id
    cdef public str logger_name

    cdef public double origin_price
    cdef public double origin_stop_price
    cdef public double origin_quantity
    cdef public double market_total_fees
    cdef public double filled_quantity
    cdef public double filled_price
    cdef public double total_cost
    cdef public double created_last_price
    cdef public double order_profitability

    cdef public double timestamp
    cdef public double creation_time
    cdef public double canceled_time
    cdef public double executed_time

    cdef public dict fee # Dict[str, Union[str, double]]

    cdef list last_prices
    cdef public list linked_orders

    cdef public object exchange_order_type # raw exchange order type, used to create order dict

    cpdef bint update(self,
            str symbol,
            str order_id=*,
            object status=*,
            double current_price=*,
            double quantity=*,
            double price=*,
            double stop_price=*,
            double quantity_filled=*,
            double filled_price=*,
            double average_price=*,
            dict fee=*,
            double total_cost=*,
            object timestamp=*,
            object linked_to=*,
            object linked_portfolio=*,
            object order_type=*)

    cdef void _update_type_from_raw(self, dict raw_order)
    cdef void _update_taker_maker(self)

    cpdef str to_string(self)
    cpdef add_linked_order(self, Order order)
    cpdef tuple get_currency_and_market(self)
    cpdef double get_total_fees(self, str currency)
    cpdef bint is_open(self)
    cpdef bint is_filled(self)
    cpdef bint is_cancelled(self)
    cpdef bint is_closed(self)
    cpdef void on_fill_actions(self)
    cpdef dict get_computed_fee(self, object forced_value=*)
    cpdef double get_profitability(self)
    cpdef double generate_executed_time(self)
    cpdef bint is_self_managed(self)
    cpdef bint update_from_raw(self, dict raw_order)
    cpdef void consider_as_filled(self)
    cpdef dict to_dict(self)
    cpdef void clear(self)
    cpdef bint is_to_be_maintained(self)
    cpdef str get_logger_name(self)

cdef object _get_sell_and_buy_types(object order_type)

cpdef tuple parse_order_type(dict raw_order)
