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

cimport octobot_trading.exchanges.exchange_manager as exchange_manager
cimport octobot_trading.util as util


cdef class Trader(util.Initializable):
    cdef dict config

    cdef public object risk
    cdef public bint allow_artificial_orders

    cdef public str trader_type_str

    cdef public bint simulate
    cdef public bint is_enabled

    cdef public object logger

    cdef public exchange_manager.ExchangeManager exchange_manager

    # methods
    cpdef void clear(self)
    cpdef str parse_order_id(self, str order_id)
    cpdef object set_risk(self, object risk)
    cpdef object convert_order_to_trade(self, object order)

    cdef bint _has_open_position(self, str symbol)
