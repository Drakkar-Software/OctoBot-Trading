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
    cdef public str source_address
    cdef public str destination_address
    cdef public str blockchain_transaction_id

    cdef public object blockchain_type
    cdef public object blockchain_transaction_status
    cdef public object quantity
    cdef public object transaction_fee

    cpdef bint is_deposit(self)
    cpdef bint is_withdraw(self)
    cpdef bint is_pending(self)
    cpdef bint is_validated(self)
