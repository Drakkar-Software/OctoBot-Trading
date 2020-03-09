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
from octobot_trading.data.position cimport Position
from octobot_trading.exchanges.exchange_manager cimport ExchangeManager
from octobot_trading.traders.trader cimport Trader
from octobot_trading.util.initializable cimport Initializable


cdef class PositionsManager(Initializable):
    cdef object logger

    cdef dict config

    cdef public bint positions_initialized

    cdef Trader trader
    cdef ExchangeManager exchange_manager

    cdef public object positions

    cdef void _reset_positions(self)
    cdef void _check_positions_size(self)
    cdef Position _create_position_from_raw(self, dict raw_position)
    cdef void _remove_oldest_positions(self, int nb_to_remove)
    cdef list _select_positions(self, object status=*, str symbol=*, int since=*, int limit=*)

    cpdef bint upsert_position(self, str position_id, dict raw_position)
    cpdef bint upsert_position_instance(self, Position position)
    cpdef list get_open_positions(self, str symbol=*, int since=*, int limit=*)
    cpdef list get_closed_positions(self, str symbol=*, int since=*, int limit=*)
