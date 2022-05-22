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
cimport octobot_trading.modes.channel as modes_channel

cdef class AbstractTradingModeProducer(modes_channel.ModeChannelProducer):
    cdef public object trading_mode
    cdef public object config
    cdef public object exchange_manager
    cdef public object final_eval
    cdef public object state
    cdef public object matrix_consumer

    cdef public str exchange_name

    cdef public int priority_level

    cpdef void flush(self)
    cpdef bint is_cryptocurrency_wildcard(self)
    cpdef bint is_symbol_wildcard(self)
    cpdef bint is_time_frame_wildcard(self)
    cpdef object get_callback(self, str chan_name)
    cpdef list get_channels_registration(self)
    cpdef object get_trigger_time_frames(self)
