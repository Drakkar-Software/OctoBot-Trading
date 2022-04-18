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
cimport octobot_trading.personal_data.orders.order as order_class
cimport octobot_trading.exchanges as exchanges
cimport octobot_trading.util as util


cdef class OrdersManager(util.Initializable):
    cdef object logger

    cdef public bint orders_initialized

    cdef exchanges.Trader trader

    cdef public object orders
    cdef public dict order_groups
    cdef public list pending_creation_orders
    cdef public bint are_exchange_orders_initialized

    cdef void _reset_orders(self)
    cdef void _check_orders_size(self)
    cdef void _remove_oldest_orders(self, int nb_to_remove)
    cdef list _select_orders(self, object state=*, str symbol=*, int since=*, int limit=*, str tag=*)
    cdef object _get_pending_order(self, object created_order, bint should_pop)

    cpdef order_class.Order get_order(self, str order_id)
    cpdef void register_pending_creation_order(self, object pending_order)
    cpdef bint has_order(self, str order_id)
    cpdef void remove_order_instance(self, order_class.Order order)
    cpdef void replace_order(self, str previous_id, order_class.Order order)
    cpdef list get_all_orders(self, str symbol=*, int since=*, int limit=*, str tag=*)
    cpdef list get_open_orders(self, str symbol=*, int since=*, int limit=*, str tag=*)
    cpdef list get_closed_orders(self, str symbol=*, int since=*, int limit=*, str tag=*)
    cpdef list get_order_from_group(self, str group_name)
    cpdef object get_or_create_group(self, object group_type, str group_name)
    cpdef void clear(self)
