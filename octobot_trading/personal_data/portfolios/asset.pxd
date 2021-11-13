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

cdef class Asset:
    cdef public str name

    cdef public object available  # Decimal
    cdef public object total  # Decimal

    cpdef void restore_available(self)
    cpdef void reset(self)
    cpdef dict to_dict(self)

    cpdef object _ensure_update_validity(self, object origin_quantity, object update_quantity)
    cpdef object _ensure_not_negative(self, object new_value, object replacement_value=*)
