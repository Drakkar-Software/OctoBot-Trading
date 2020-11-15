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

cimport octobot_trading.util as util

cdef class Position(util.Initializable):
    cdef object trader
    cdef object exchange_manager

    cdef public str symbol
    cdef public str currency
    cdef public str market
    cdef public str position_id

    cdef public object status # PositionStatus
    cdef public object side # PositionSide

    cdef public int leverage

    cdef public double entry_price
    cdef public double mark_price
    cdef public double liquidation_price
    cdef public double quantity
    cdef public double value
    cdef public double unrealised_pnl
    cdef public double realised_pnl

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
                      double entry_price,
                      double mark_price,
                      double liquidation_price,
                      double quantity,
                      double value,
                      double margin,
                      double unrealised_pnl,
                      double realised_pnl,
                      int leverage,
                      object status=*,
                      object side=*)
    cdef bint _check_for_liquidation(self)
    cdef bint _should_change(self, object original_value, object new_value)

    cpdef dict to_dict(self)

    cpdef bint update_position_from_raw(self, dict raw_position)
    cpdef bint is_liquidated(self)

cdef class ShortPosition(Position):
    cdef bint _check_for_liquidation(self)

cdef class LongPosition(Position):
    cdef bint _check_for_liquidation(self)
