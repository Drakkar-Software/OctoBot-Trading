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

import octobot_trading.enums as enums
import octobot_trading.personal_data.transactions.transaction as transaction


class RealisedPnlTransaction(transaction.Transaction):
    def __init__(self, exchange_name, creation_time, transaction_type, currency, symbol, realised_pnl):
        super().__init__(exchange_name, creation_time, transaction_type, currency, symbol=symbol)
        self.realised_pnl = realised_pnl
        self.transaction_id = f"{self.exchange_name}" \
                              f"-{str(uuid.uuid4())[:4]}" \
                              f"-{self.symbol}" \
                              f"-{str(self.creation_time)}" \
                              f"{'-closed' if self.is_closed_pnl() else ''}"

    def is_closed_pnl(self):
        return self.transaction_type is enums.TransactionType.CLOSE_REALISED_PNL
