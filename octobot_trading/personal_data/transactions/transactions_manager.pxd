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


cdef class TransactionsManager(util.Initializable):
    cdef object logger

    cdef public object transactions

    cdef void _check_transactions_size(self)
    cdef void _reset_transactions(self)
    cdef void _remove_oldest_transactions(self, int nb_to_remove)

    cpdef object get_transaction(self, str transaction_id)
    cpdef object update_transaction_id(self, str transaction_id, str new_transaction_id, bint replace_if_exists=*)  # needs object to forward exceptions
    cpdef object insert_transaction_instance(self, object transaction, bint replace_if_exists=*)  # needs object to forward exceptions
    cpdef void clear(self)
