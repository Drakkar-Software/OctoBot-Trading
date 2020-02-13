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
from octobot_commons.tentacles_management.abstract_tentacle cimport AbstractTentacle

cdef class AbstractTradingMode(AbstractTentacle):
    cdef public dict config

    cdef public object exchange_manager
    cdef public object trading_config

    cdef public bint enabled

    cdef public str cryptocurrency
    cdef public str symbol
    cdef public str time_frame

    cdef public list producers
    cdef public list consumers

    cpdef void load_config(self)
    cpdef void set_default_config(self)

    cpdef list get_parent_trading_mode_classes(cls, object higher_parent_class_limit=*)

    cpdef bint get_is_cryptocurrency_wildcard(cls)
    cpdef bint get_is_symbol_wildcard(cls)
    cpdef bint get_is_time_frame_wildcard(cls)
