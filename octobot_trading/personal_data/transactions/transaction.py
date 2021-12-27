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
import uuid

import octobot_commons.logging as logging


class Transaction:

    def __init__(self, exchange_name, creation_time, transaction_type, currency, symbol=None, transaction_id=None):
        self.logger = logging.get_logger(self.__class__.__name__)
        self.transaction_id = transaction_id
        self.transaction_type = transaction_type
        self.creation_time = creation_time

        self.exchange_name = exchange_name
        self.symbol = symbol
        self.currency = currency

        # generate default transaction id
        if self.transaction_id is None:
            self.transaction_id = str(uuid.uuid4())

    def set_transaction_id(self, new_id):
        """
        Shouldn't be called outside of TransactionsManager.update_transaction_id
        to maintain TransactionsManager.transactions integrity
        :param new_id: the new transaction id
        """
        self.transaction_id = new_id
