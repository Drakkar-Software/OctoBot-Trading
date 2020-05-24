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
from octobot_trading.util.initializable cimport Initializable


cdef class PriceEventsManager(Initializable):
    cdef object logger

    cdef list events

    cpdef void reset(self)
    cpdef void handle_recent_trades(self, list recent_trades)
    cpdef void handle_price(self, double price, double timestamp)
    cpdef object add_event(self, double price, double timestamp, bint trigger_above) # return asyncio.Event

    cdef int _remove_and_set_event(self, int event_index, object event_to_set) # return int to propagate errors
    cdef list _check_events(self, double price, double timestamp)

cdef tuple _new_price_event(double price, double timestamp, bint trigger_above)
