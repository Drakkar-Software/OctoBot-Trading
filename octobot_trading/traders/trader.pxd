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


cdef class Trader(Initializable):
    cdef float risk

    cdef public str trader_type_str

    cdef public bint simulate
    cdef public bint enable
    cdef public bint loaded_previous_state

    cdef object exchange
    cdef object config
    cdef object order_refresh_time
    cdef public object notifier
    cdef public object logger
    cdef public object exchange_personal_data
    cdef public object previous_state_manager

    cdef public list trading_modes
