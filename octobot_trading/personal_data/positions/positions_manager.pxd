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
cimport octobot_trading.personal_data.positions as positions_personal_data
cimport octobot_trading.util as util


cdef class PositionsManager(util.Initializable):
    cdef object logger

    cdef public bint positions_initialized

    cdef object trader

    cdef public object positions

    cdef void _reset_positions(self)
    cdef list _select_positions(self, str symbol=*)
    cdef object _create_symbol_position(self, str symbol)

    cpdef bint upsert_position_instance(self, positions_personal_data.Position position)
    cpdef positions_personal_data.Position get_symbol_position(self, str symbol)
    cpdef positions_personal_data.Position get_position_by_id(self, str position_id)
    cpdef int get_symbol_leverage(self, str symbol)
    cpdef object get_symbol_margin_type(self, str symbol)
    cpdef void clear(self)
