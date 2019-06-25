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


""" Order class will represent an open order in the specified exchange
In simulation it will also define rules to be filled / canceled
It is also use to store creation & fill values of the order """
from octobot_trading.util.initializable cimport Initializable

cdef class Position(Initializable):
    cdef public object trader

    cdef public bint is_open

    cdef public str symbol
    cdef public str currency
    cdef public str market
    cdef public str position_id

    cdef public int leverage

    cdef public float entry_price
    cdef public float mark_price
    cdef public float quantity
    cdef public float liquidation_price
    cdef public float unrealised_pnl

    cdef public float timestamp
    cdef public float creation_time
    cdef public float canceled_time
    cdef public float executed_time

    # to use Non-trivial keyword arguments
    # cpdef bint update(self,
    #                   str position_id,
    #                   str symbol,
    #                   str currency,
    #                   str market,
    #                   float timestamp,
    #                   float entry_price,
    #                   float mark_price,
    #                   float quantity,
    #                   float liquidation_price,
    #                   float unrealised_pnl,
    #                   int leverage,
    #                   bint is_open)
