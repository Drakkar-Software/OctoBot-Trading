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

cimport octobot_trading.personal_data.transactions.transaction as transaction

cdef class RealisedPnlTransaction(transaction.Transaction):
    cdef readonly object realised_pnl
    cdef readonly object closed_quantity
    cdef readonly object cumulated_closed_quantity
    cdef readonly double first_entry_time
    cdef readonly object average_entry_price
    cdef readonly object average_exit_price
    cdef readonly object order_exit_price
    cdef readonly object leverage
    cdef readonly object trigger_source
    cdef readonly object side

    cpdef bint is_closed_pnl(self)
