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
cimport octobot_trading.util as util


cdef class TradesManager(util.Initializable):
    cdef object logger
    cdef object trader

    cdef public object trades

    cdef public bint trades_initialized

    cdef void _check_trades_size(self)
    cdef void _reset_trades(self)
    cdef void _remove_oldest_trades(self, int nb_to_remove)

    cpdef object get_trade(self, str trade_id)
    cpdef bint upsert_trade(self, str trade_id, dict raw_trade)
    cpdef void upsert_trade_instance(self, object trade)
    cpdef bint has_closing_trade_with_order_id(self, str order_id)
    cpdef dict get_total_paid_fees(self)
    cpdef void clear(self)
