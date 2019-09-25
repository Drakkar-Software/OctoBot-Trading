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
    cdef public dict strategy_instances_by_classes

    cdef public object exchange_manager
    cdef public object trading_config

    cpdef void load_config(self)
    cpdef void set_default_config(self)

    cpdef tuple get_required_strategies_names_and_count(cls, object trading_mode_config=*)
    cpdef list get_parent_trading_mode_classes(cls, object higher_parent_class_limit=*)
    cpdef object get_default_strategies(cls)
    cpdef int get_required_strategies_count(cls, dict config)
