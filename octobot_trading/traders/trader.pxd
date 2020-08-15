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
from octobot_trading.data.trade cimport Trade
from octobot_trading.exchanges.exchange_manager cimport ExchangeManager
from octobot_trading.util.initializable cimport Initializable


cdef class Trader(Initializable):
    cdef dict config

    cdef public double risk

    cdef public str trader_type_str

    cdef public bint simulate
    cdef public bint is_enabled

    cdef public object logger

    cdef public ExchangeManager exchange_manager

    # methods
    cpdef str parse_order_id(self, str order_id)
    cpdef double set_risk(self, double risk)
    cpdef Trade convert_order_to_trade(self, Order order)
