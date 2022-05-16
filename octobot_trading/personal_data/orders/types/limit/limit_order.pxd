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
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
cimport octobot_trading.personal_data.orders.order as order_class

cdef class LimitOrder(order_class.Order):
    cdef object limit_price_hit_event # object is asyncio.Event
    cdef object wait_for_hit_event_task # object is asyncio.Task

    cdef bint trigger_above
    cdef public bint allow_instant_fill

    cpdef str _filled_maker_or_taker(self)
    # return object to allow exception raising
    cdef object _create_hit_event(self, object price_time)
    cdef object _create_hit_task(self)
    cdef object _reset_events(self, object price_time)
    cdef object _clear_event_and_tasks(self)
