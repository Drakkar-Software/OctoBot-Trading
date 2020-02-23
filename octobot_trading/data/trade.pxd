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
from octobot_trading.data.order cimport Order
from octobot_trading.exchanges.exchange_manager cimport ExchangeManager
from octobot_trading.traders.trader cimport Trader

cdef class Trade:
    cdef public Trader trader
    cdef public ExchangeManager exchange_manager

    cdef public object side # TradeOrderSide
    cdef public object status # OrderStatus
    cdef public object trade_type # TraderOrderType

    cdef public str symbol
    cdef public str currency
    cdef public str market
    cdef public str taker_or_maker
    cdef public str trade_id
    cdef public bint simulated

    cdef public double origin_price
    cdef public double origin_quantity
    cdef public double market_total_fees
    cdef public double executed_quantity
    cdef public double executed_price
    cdef public double total_cost
    cdef public double trade_profitability

    cdef public double timestamp
    cdef public double creation_time
    cdef public double canceled_time
    cdef public double executed_time

    cdef public dict fee # Dict[str, Union[str, double]]

    cdef public object exchange_trade_type # raw exchange trade type, used to create trade dict

    cpdef void update_from_order(self,
                                 Order order,
                                 double canceled_time=*,
                                 double creation_time=*,
                                 double executed_time=*)
