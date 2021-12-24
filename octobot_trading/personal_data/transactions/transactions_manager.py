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

import octobot_trading.util as util


class TransactionsManager(util.Initializable):
    MAX_TRANSACTIONS_COUNT = 100000

    def __init__(self):
        super().__init__()
        self.logger = logging.get_logger(self.__class__.__name__)
        self.transactions_initialized = False
        self.transactions = collections.OrderedDict()

    async def initialize_impl(self):
        self._reset_transactions()
        self.transactions_initialized = True

    def upsert_transaction_instance(self, transaction):
        if transaction.transaction_id not in self.transactions:
            self.transactions[transaction.transaction_id] = transaction
            self._check_transactions_size()

    def get_transactions(self, transaction_id):
        return self.transactions[transaction_id]

    # private
    def _check_transactions_size(self):
        if len(self.transactions) > self.MAX_TRANSACTIONS_COUNT:
            self._remove_oldest_transactions(int(self.MAX_TRANSACTIONS_COUNT / 10))

    def _reset_transactions(self):
        self.transactions_initialized = False
        self.transactions = collections.OrderedDict()

    def _remove_oldest_transactions(self, nb_to_remove):
        for _ in range(nb_to_remove):
            self.transactions.popitem(last=False)

    def clear(self):
        self._reset_transactions()
