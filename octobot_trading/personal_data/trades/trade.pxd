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

cdef class Trade:
    cdef public object trader
    cdef public object exchange_manager

    cdef public object side # TradeOrderSide
    cdef public object status # OrderStatus
    cdef public object trade_type # TraderOrderType

    cdef public str symbol
    cdef public str currency
    cdef public str market
    cdef public str taker_or_maker
    cdef public str trade_id
    cdef public str origin_order_id
    cdef public bint simulated
    cdef public bint is_closing_order

    cdef public object origin_price
    cdef public object origin_quantity
    cdef public object executed_quantity
    cdef public object executed_price
    cdef public object total_cost
    cdef public object trade_profitability

    cdef public double timestamp
    cdef public double creation_time
    cdef public double canceled_time
    cdef public double executed_time

    cdef public dict fee # Dict[str, Union[str, decimal.Decimal]]

    cdef public object exchange_trade_type # raw exchange trade type, used to create trade dict

    cpdef double get_time(self)
    cpdef object get_quantity(self)
    cpdef void update_from_order(self,
                                 object order,
                                 double canceled_time=*,
                                 double creation_time=*,
                                 double executed_time=*)
