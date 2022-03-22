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


class FeeTransaction(transaction.Transaction):
    def __init__(self, exchange_name, creation_time, transaction_type, currency, symbol, quantity,
                 order_id=None,
                 funding_rate=constants.ZERO):
        self.quantity = quantity
        self.order_id = order_id
        self.funding_rate = funding_rate
        super().__init__(exchange_name, creation_time, transaction_type, currency, symbol=symbol)
        self.transaction_id = f"{self.exchange_name}" \
                              f"-{self.order_id if self.order_id else str(uuid.uuid4())}" \
                              f"-{self.symbol}" \
                              f"-{str(self.creation_time)}"

    def is_funding_fee(self):
        return self.transaction_type is enums.TransactionType.FUNDING_FEE

    def is_trading_fee(self):
        return self.transaction_type is enums.TransactionType.TRADING_FEE
