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
    cdef positions_personal_data.Position _get_or_create_position(self, str symbol, object side)
    cdef object _create_symbol_position(self, str symbol, str position_id)
    cdef str _generate_position_id(self, str symbol, object side, object expiration_time=*)
    cdef list _get_symbol_positions(self, str symbol)

    cpdef positions_personal_data.Position get_symbol_position(self, str symbol, object side)
    cpdef positions_personal_data.Position get_order_position(self, object order, object contract=*)
    cpdef list get_symbol_positions(self, str symbol=*)
    cpdef bint upsert_position_instance(self, positions_personal_data.Position position)
    cpdef void clear(self)
