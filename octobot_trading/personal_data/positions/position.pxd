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

cimport octobot_trading.personal_data.positions.position_state as positions_states
cimport octobot_trading.util as util

cdef class Position(util.Initializable):
    cdef object trader
    cdef object exchange_manager

    cdef public bint simulated

    cdef public str symbol
    cdef public str currency
    cdef public str market
    cdef public str position_id

    cdef public object status # PositionStatus
    cdef public object margin_type # MarginType
    cdef public object side # PositionSide

    cdef public positions_states.PositionState state

    cdef public int leverage

    cdef public object entry_price
    cdef public object mark_price
    cdef public object liquidation_price
    cdef public object quantity
    cdef public object value
    cdef public object margin
    cdef public object unrealised_pnl
    cdef public object realised_pnl

    cdef public double timestamp
    cdef public double creation_time
    cdef public double canceled_time
    cdef public double executed_time

    cdef bint _update(self,
                      str position_id,
                      str symbol,
                      str currency,
                      str market,
                      double timestamp,
                      object entry_price,
                      object mark_price,
                      object liquidation_price,
                      object quantity,
                      object value,
                      object margin,
                      object unrealised_pnl,
                      object realised_pnl,
                      int leverage,
                      object margin_type,
                      object status=*,
                      object side=*)
    cdef bint _check_for_liquidation(self)
    cdef bint _switch_side_if_necessary(self)
    cdef bint _should_change(self, object original_value, object new_value)

    cpdef dict to_dict(self)

    cpdef bint update_from_raw(self, dict raw_position)
    cpdef bint is_liquidated(self)
    cpdef bint is_long(self)
    cpdef bint is_short(self)
    cpdef bint is_open(self)
    cpdef str to_string(self)
    cpdef void clear(self)

cpdef object parse_position_type(dict raw_position)
