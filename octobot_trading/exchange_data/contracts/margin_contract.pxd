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


cdef class MarginContract:
    cdef readonly str pair

    cdef public object margin_type

    cdef readonly object contract_size
    cdef readonly object current_leverage
    cdef readonly object maximum_leverage

    cdef readonly dict risk_limit

    cpdef bint is_isolated(self)
    cpdef bint check_leverage_update(self, object new_leverage)
    cpdef void set_current_leverage(self, object new_leverage)
    cpdef void set_margin_type(self, bint is_isolated=*, bint is_cross=*)
