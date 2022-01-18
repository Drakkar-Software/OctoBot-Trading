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
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
import collections

import octobot_commons.logging as logging

import octobot_trading.errors as errors
import octobot_trading.util as util


class TransactionsManager(util.Initializable):
    MAX_TRANSACTIONS_COUNT = 100000

    def __init__(self):
        super().__init__()
        self.logger = logging.get_logger(self.__class__.__name__)
        self.transactions = collections.OrderedDict()

    async def initialize_impl(self):
        self._reset_transactions()

    def insert_transaction_instance(self, transaction, replace_if_exists=False):
        """
        Add the transaction instance to self.transactions by its transaction_id
        Can raise DuplicateTransactionIdError if a transaction already exists
        with the same transaction_id (when not replacing it with :replace_if_exists:)
        :param transaction:
        :param replace_if_exists: When True, replaces the transaction if a transaction has the same transaction_id
        """
        if transaction.transaction_id not in self.transactions or replace_if_exists:
            self.transactions[transaction.transaction_id] = transaction
            self._check_transactions_size()
        else:
            raise errors.DuplicateTransactionIdError(
                f"Transaction with id '{transaction.transaction_id}' already exists")

    def get_transaction(self, transaction_id):
        """
        Return the transaction instance with :transaction_id: as transaction_id
        Can raise KeyError when transaction_id doesn't exist
        :param transaction_id: the transaction id
        :return: the transaction with the id :transaction_id:
        """
        return self.transactions[transaction_id]

    def update_transaction_id(self, transaction_id, new_transaction_id, replace_if_exists=False):
        """
        Update a transaction by id
        Can raise KeyError when initial transaction doesn't exist
        Can raise DuplicateTransactionIdError when the :new_transaction_id: is already used
        :param transaction_id: the transaction id to update
        :param new_transaction_id: the transaction id to set
        :param replace_if_exists: when True, replace the transaction with :new_transaction_id: if exist
        """
        transaction = self.get_transaction(transaction_id)
        transaction.set_transaction_id(new_transaction_id)
        try:
            self.insert_transaction_instance(transaction, replace_if_exists=replace_if_exists)
            self.transactions.pop(transaction_id)
        except errors.DuplicateTransactionIdError as e:
            transaction.set_transaction_id(transaction_id)
            raise errors.DuplicateTransactionIdError from e

    # private
    def _check_transactions_size(self):
        if len(self.transactions) > self.MAX_TRANSACTIONS_COUNT:
            self._remove_oldest_transactions(int(self.MAX_TRANSACTIONS_COUNT / 10))

    def _reset_transactions(self):
        self.transactions = collections.OrderedDict()

    def _remove_oldest_transactions(self, nb_to_remove):
        for _ in range(nb_to_remove):
            self.transactions.popitem(last=False)

    def clear(self):
        self._reset_transactions()
