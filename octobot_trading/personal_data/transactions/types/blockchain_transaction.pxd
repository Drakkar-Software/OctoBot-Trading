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

cdef class BlockchainTransaction(transaction.Transaction):
    cdef readonly str source_address
    cdef readonly str destination_address
    cdef readonly str blockchain_transaction_id

    cdef readonly object blockchain_type
    cdef readonly object blockchain_transaction_status
    cdef readonly object quantity
    cdef readonly object transaction_fee

    cpdef bint is_deposit(self)
    cpdef bint is_withdrawal(self)
    cpdef bint is_pending(self)
    cpdef bint is_validated(self)
