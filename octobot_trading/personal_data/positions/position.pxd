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
    cdef public str logger_name

    cdef public object status # PositionStatus
    cdef public object margin_type # MarginType
    cdef public object side # PositionSide
    cdef public object symbol_contract # FutureContract

    cdef public positions_states.PositionState state

    cdef public object leverage
    cdef public object entry_price
    cdef public object mark_price
    cdef public object liquidation_price
    cdef public object quantity
    cdef public object size
    cdef public object value
    cdef public object margin
    cdef public object initial_margin
    cdef public object unrealised_pnl
    cdef public object realised_pnl
    cdef public object fee_to_close

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
                      object size,
                      object value,
                      object margin,
                      object unrealised_pnl,
                      object realised_pnl,
                      object leverage,
                      object margin_type,
                      object status=*,
                      object side=*)
    cdef bint _should_change(self, object original_value, object new_value)
    cdef void _update_quantity_and_mark_price(self, object update_quantity=*, object mark_price=*)
    cdef void _update_mark_price(self, object mark_price)
    cdef void _update_entry_price_if_necessary(self, object mark_price)
    cdef void _update_quantity_or_size_if_necessary(self)
    cdef void _update_quantity(self, object update_size)
    cdef void _update_size(self)
    cdef void _update_margin(self)
    cdef void _update_side(self)

    cpdef void update_value(self)
    cpdef void update_pnl(self)
    cpdef void update_initial_margin(self)
    cpdef object get_maintenance_margin_rate(self)
    cpdef object get_initial_margin_rate(self)
    cpdef object calculate_maintenance_margin(self)
    cpdef bint update_from_raw(self, dict raw_position)
    cpdef void update_liquidation_price(self)
    cpdef void update_cross_liquidation_price(self)
    cpdef void update_isolated_liquidation_price(self)
    cpdef object get_bankruptcy_price(self, bint with_mark_price=*)
    cpdef object get_maker_fee(self)
    cpdef object get_taker_fee(self)
    cpdef object get_two_way_taker_fee(self)
    cpdef object get_order_cost(self)
    cpdef object get_fee_to_open(self)
    cpdef void update_fee_to_close(self)
    cpdef bint is_open(self)
    cpdef bint is_liquidated(self)
    cpdef bint is_refreshing(self)
    cpdef bint is_long(self)
    cpdef bint is_short(self)
    cpdef bint is_idle(self)
    cpdef object get_unrealised_pnl_percent(self)
    cpdef str to_string(self)
    cpdef dict to_dict(self)
    cpdef void clear(self)
    cpdef str get_logger_name(self)
