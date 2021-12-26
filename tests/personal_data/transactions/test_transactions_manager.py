#  Drakkar-Software OctoBot
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
import decimal
import uuid

import pytest

import octobot_trading.enums as enums
import octobot_trading.constants as constants
import octobot_trading.personal_data.transactions.types as transaction_types

from tests.exchanges import backtesting_trader, backtesting_config, backtesting_exchange_manager, fake_backtesting
from tests import event_loop

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

TRANSACTION_SYMBOL = "BTC/USDT"
TRANSACTION_CURRENCY = "BTC"


async def test_initialized(backtesting_trader):
    _, exchange_manager, _ = backtesting_trader
    assert exchange_manager.exchange_personal_data.transactions_manager.is_initialized


async def test_upsert_transaction_instance(backtesting_trader):
    _, exchange_manager, _ = backtesting_trader
    assert len(exchange_manager.exchange_personal_data.transactions_manager.transactions) == 0
    t_id = str(uuid.uuid4())
    t_id_2 = str(uuid.uuid4())
    transaction = transaction_types.RealisedPnlTransaction(
        exchange_name=exchange_manager.exchange_name,
        creation_time=exchange_manager.exchange.get_exchange_current_time(),
        currency=TRANSACTION_CURRENCY,
        symbol=TRANSACTION_SYMBOL,
        realised_pnl=constants.ZERO,
        is_closed_pnl=False)
    transaction.transaction_id = t_id
    transaction_2 = transaction_types.BlockchainTransaction(
        exchange_name=exchange_manager.exchange_name,
        creation_time=exchange_manager.exchange.get_exchange_current_time(),
        currency=TRANSACTION_CURRENCY,
        blockchain_type="Test",
        blockchain_transaction_id=t_id,
        blockchain_transaction_status=enums.BlockchainTransactionStatus.CONFIRMING,
        source_address="0x123456789",
        destination_address=None,
        quantity=decimal.Decimal(50),
        transaction_fee=decimal.Decimal(0.1)
    )
    transaction_2.transaction_id = t_id

    # succeed to upsert unknown transaction
    assert len(exchange_manager.exchange_personal_data.transactions_manager.transactions) == 0
    exchange_manager.exchange_personal_data.transactions_manager.upsert_transaction_instance(transaction)
    assert len(exchange_manager.exchange_personal_data.transactions_manager.transactions) == 1

    # can't add transaction with the same transaction id without replacing it --> ValueError
    with pytest.raises(ValueError):
        exchange_manager.exchange_personal_data.transactions_manager.upsert_transaction_instance(transaction_2)
    assert len(exchange_manager.exchange_personal_data.transactions_manager.transactions) == 1

    # can replace a transaction with the same transaction id
    exchange_manager.exchange_personal_data.transactions_manager.upsert_transaction_instance(transaction_2,
                                                                                             replace_if_exists=True)
    assert len(exchange_manager.exchange_personal_data.transactions_manager.transactions) == 1

    # succeed to upsert a transaction with a new id
    transaction.transaction_id = t_id_2
    exchange_manager.exchange_personal_data.transactions_manager.upsert_transaction_instance(transaction)
    assert len(exchange_manager.exchange_personal_data.transactions_manager.transactions) == 2

    # check transaction instances
    assert list(exchange_manager.exchange_personal_data.transactions_manager.transactions.values())[0] is transaction_2
    assert list(exchange_manager.exchange_personal_data.transactions_manager.transactions.values())[-1] is transaction


async def test_get_transactions(backtesting_trader):
    _, exchange_manager, _ = backtesting_trader
    assert len(exchange_manager.exchange_personal_data.transactions_manager.transactions) == 0
    transaction = transaction_types.RealisedPnlTransaction(
        exchange_name=exchange_manager.exchange_name,
        creation_time=exchange_manager.exchange.get_exchange_current_time(),
        currency=TRANSACTION_CURRENCY,
        symbol=TRANSACTION_SYMBOL,
        realised_pnl=constants.ZERO,
        is_closed_pnl=False)
    transaction_2 = transaction_types.RealisedPnlTransaction(
        exchange_name=exchange_manager.exchange_name,
        creation_time=exchange_manager.exchange.get_exchange_current_time(),
        currency=TRANSACTION_CURRENCY,
        symbol=TRANSACTION_SYMBOL,
        realised_pnl=constants.ZERO,
        is_closed_pnl=False)
    exchange_manager.exchange_personal_data.transactions_manager.upsert_transaction_instance(transaction)

    # succeed to return transaction instance
    assert exchange_manager.exchange_personal_data.transactions_manager. \
               get_transactions(transaction.transaction_id) is transaction

    # can't get unknown transaction id
    with pytest.raises(KeyError):
        exchange_manager.exchange_personal_data.transactions_manager.get_transactions(str(uuid.uuid4()))

    # can't get a transaction which has not been added
    with pytest.raises(KeyError):
        exchange_manager.exchange_personal_data.transactions_manager.get_transactions(transaction_2.transaction_id)

    # succeed to return transaction instances
    exchange_manager.exchange_personal_data.transactions_manager.upsert_transaction_instance(transaction_2)
    assert exchange_manager.exchange_personal_data.transactions_manager. \
               get_transactions(transaction.transaction_id) is transaction
    assert exchange_manager.exchange_personal_data.transactions_manager. \
               get_transactions(transaction_2.transaction_id) is transaction_2
