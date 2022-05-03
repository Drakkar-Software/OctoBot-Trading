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
cimport octobot_trading.util as util


cdef class PriceEventsManager(util.Initializable):
    cdef object logger

    cdef list events
    cdef list _last_recent_prices

    cpdef void reset(self)
    cpdef void handle_recent_trades(self, list recent_trades)
    cpdef void handle_price(self, object price, double timestamp)
    cpdef object new_event(self, object price, double timestamp, bint trigger_above, bint allow_instant_fill=*) # return asyncio.Event
    cpdef object remove_event(self, object event_to_remove) # object is an asyncio.Event
    cpdef void clear_recent_prices(self)

    cdef bint _is_triggered_by_last_recent_prices(self, object price, double timestamp, bint trigger_above)
    cdef void _add_recent_price(self, object price, double timestamp)
    cdef object _remove_and_set_event(self, object event_to_set) # return to propagate errors
    cdef object _remove_event(self, object event_to_remove) # object is an asyncio.Event
    cdef list _check_events(self, object price, double timestamp)

cdef tuple _new_price_event(object price, double timestamp, bint trigger_above)
