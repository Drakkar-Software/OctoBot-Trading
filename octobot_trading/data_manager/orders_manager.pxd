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
from octobot_trading.data.order cimport Order
from octobot_trading.exchanges.exchange_manager cimport ExchangeManager
from octobot_trading.traders.trader cimport Trader
from octobot_trading.util.initializable cimport Initializable


cdef class OrdersManager(Initializable):
    cdef object logger
    cdef dict config

    cdef public bint orders_initialized

    cdef Trader trader
    cdef ExchangeManager exchange_manager

    cdef public object orders

    cdef void _reset_orders(self)
    cdef void _check_orders_size(self)
    cdef void _remove_oldest_orders(self, int nb_to_remove)
    cdef list _select_orders(self, object state=*, str symbol=*, int since=*, int limit=*)

    cpdef void update_order_attribute(self, str order_id, str key, object value)
    cpdef Order get_order(self, str order_id)
    cpdef bint upsert_order_instance(self, Order order)
    cpdef bint has_order(self, str order_id)
    cpdef void remove_order_instance(self, Order order)
    cpdef list get_all_orders(self, str symbol=*, int since=*, int limit=*)
    cpdef list get_open_orders(self, str symbol=*, int since=*, int limit=*)
    cpdef list get_closed_orders(self, str symbol=*, int since=*, int limit=*)
    cpdef void clear(self)
