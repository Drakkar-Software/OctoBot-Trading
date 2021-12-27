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

import octobot_trading.constants as constants
import octobot_trading.enums as enums
import octobot_trading.personal_data.transactions.transaction as transaction


class BlockchainTransaction(transaction.Transaction):
    def __init__(self, exchange_name, creation_time, transaction_type, currency, blockchain_type,
                 blockchain_transaction_id,
                 blockchain_transaction_status=enums.BlockchainTransactionStatus.CREATED,
                 source_address=None,
                 destination_address=None,
                 quantity=constants.ZERO,
                 transaction_fee=constants.ZERO):
        self.source_address = source_address
        self.destination_address = destination_address
        self.blockchain_transaction_id = blockchain_transaction_id
        self.blockchain_type = blockchain_type
        self.blockchain_transaction_status = blockchain_transaction_status
        self.quantity = quantity
        self.transaction_fee = transaction_fee
        super().__init__(exchange_name, creation_time, transaction_type, currency=currency)
        self.transaction_id = self.blockchain_transaction_id if self.blockchain_transaction_id else str(uuid.uuid4())

    def is_deposit(self):
        return self.transaction_type is enums.TransactionType.BLOCKCHAIN_DEPOSIT

    def is_withdrawal(self):
        return self.transaction_type is enums.TransactionType.BLOCKCHAIN_WITHDRAWAL

    def is_pending(self):
        return self.blockchain_transaction_status is enums.BlockchainTransactionStatus.CONFIRMING

    def is_validated(self):
        return self.blockchain_transaction_status is enums.BlockchainTransactionStatus.SUCCESS
