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
#  License along with this library
import octobot_commons.enums as commons_enums
import octobot_commons.databases as commons_databases

import octobot_trading.storage.abstract_storage as abstract_storage


class TransactionsStorage(abstract_storage.AbstractStorage):
    IS_LIVE_CONSUMER = False
    HISTORY_TABLE = commons_enums.DBTables.TRANSACTIONS.value

    async def _store_history(self):
        transactions = [
            transaction
            for transaction in self.exchange_manager.exchange_personal_data.transactions_manager.transactions.values()
        ]
        y_data = self.plot_settings.y_data or [0] * len(transactions)
        await self._get_db().log_many(
            self.HISTORY_TABLE,
            [
                _format_transaction(
                    transaction,
                    self.exchange_manager,
                    self.plot_settings.chart,
                    self.plot_settings.x_multiplier,
                    self.plot_settings.kind,
                    self.plot_settings.mode,
                    y_data[index]
                )
                for index, transaction in enumerate(transactions)
            ]
        )

    def _get_db(self):
        return commons_databases.RunDatabasesProvider.instance().get_transactions_db(
            self.exchange_manager.bot_id,
            self.exchange_manager.exchange_name
        )


def _format_transaction(transaction, exchange_manager, chart, x_multiplier, kind, mode, y_data):
    return {
        "x": transaction.creation_time * x_multiplier,
        "type": transaction.transaction_type.value,
        "id": transaction.transaction_id,
        "symbol": transaction.symbol,
        "trading_mode": exchange_manager.trading_modes[0].get_name(),
        "currency": transaction.currency,
        "quantity": float(transaction.quantity) if hasattr(transaction, "quantity") else None,
        "order_id": transaction.order_id if hasattr(transaction, "order_id") else None,
        "funding_rate": float(transaction.funding_rate) if hasattr(transaction, "funding_rate") else None,
        "realised_pnl": float(transaction.realised_pnl) if hasattr(transaction, "realised_pnl") else None,
        "transaction_fee": float(transaction.transaction_fee) if hasattr(transaction, "transaction_fee") else None,
        "closed_quantity": float(transaction.closed_quantity) if hasattr(transaction, "closed_quantity") else None,
        "cumulated_closed_quantity": float(transaction.cumulated_closed_quantity)
        if hasattr(transaction, "cumulated_closed_quantity") else None,
        "first_entry_time": float(transaction.first_entry_time) * x_multiplier
        if hasattr(transaction, "first_entry_time") else None,
        "average_entry_price": float(transaction.average_entry_price)
        if hasattr(transaction, "average_entry_price") else None,
        "average_exit_price": float(transaction.average_exit_price)
        if hasattr(transaction, "average_exit_price") else None,
        "order_exit_price": float(transaction.order_exit_price)
        if hasattr(transaction, "order_exit_price") else None,
        "leverage": float(transaction.leverage) if hasattr(transaction, "leverage") else None,
        "trigger_source": transaction.trigger_source.value if hasattr(transaction, "trigger_source") else None,
        "side": transaction.side.value if hasattr(transaction, "side") else None,
        "y": y_data,
        "chart": chart,
        "kind": kind,
        "mode": mode
    }
