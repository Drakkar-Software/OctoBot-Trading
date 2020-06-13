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

from octobot_trading.data.order cimport Order


cdef class TrailingStopOrder(Order):
    cdef object trailing_stop_price_hit_event # object is asyncio.Event
    cdef object trailing_price_hit_event # object is asyncio.Event
    cdef object wait_for_stop_price_hit_event_task # object is asyncio.Event
    cdef object wait_for_price_hit_event_task # object is asyncio.Event
    cdef public double trailing_percent

    cdef void _create_hit_events(self, object price_events_manager,
                                 double new_price,
                                 double new_price_time)
    cdef double _calculate_stop_price(self, double new_price)
    cdef void _create_hit_tasks(self)
    cdef void _remove_events(self, object price_events_manager)
    cdef void _clear_event_and_tasks(self)
    cdef void _cancel_hit_tasks(self)
