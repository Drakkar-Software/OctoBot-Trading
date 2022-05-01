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

import time

import pytest

import octobot_trading.enums as enums
import octobot_trading.constants as constants
import octobot_trading.personal_data.transactions.transaction_factory as transaction_factory

from tests.exchanges import backtesting_trader, backtesting_config, backtesting_exchange_manager, fake_backtesting
from tests import event_loop

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

TRANSACTION_SYMBOL = "BTC/USDT"
TRANSACTION_CURRENCY = "BTC"


async def test_create_blockchain_transaction(backtesting_trader):
    _, exchange_manager, _ = backtesting_trader
    assert len(exchange_manager.exchange_personal_data.transactions_manager.transactions) == 0
    t_id = str(uuid.uuid4())
    transaction = transaction_factory.create_blockchain_transaction(exchange_manager,
                                                                    is_deposit=True,
                                                                    currency=TRANSACTION_CURRENCY,
                                                                    blockchain_type=enums.BlockchainTypes.UNKNOWN.value,
                                                                    blockchain_transaction_id=t_id,
                                                                    blockchain_transaction_status=enums.BlockchainTransactionStatus.CONFIRMING,
                                                                    source_address="0x123456789",
                                                                    quantity=decimal.Decimal(50),
                                                                    transaction_fee=decimal.Decimal(0.1))
    assert transaction.currency == TRANSACTION_CURRENCY
    assert transaction.creation_time <= time.time()
    assert transaction.transaction_id == t_id
    assert transaction.blockchain_transaction_id == t_id
    assert transaction.blockchain_transaction_status is enums.BlockchainTransactionStatus.CONFIRMING
    assert transaction.source_address == "0x123456789"
    assert transaction.quantity == decimal.Decimal(50)
    assert transaction.transaction_fee == decimal.Decimal(0.1)
    assert transaction.is_deposit()
    assert not transaction.is_withdrawal()
    assert not transaction.is_validated()
    assert transaction.is_pending()
    assert len(exchange_manager.exchange_personal_data.transactions_manager.transactions) == 1


async def test_create_realised_pnl_transaction(backtesting_trader):
    _, exchange_manager, _ = backtesting_trader
    transaction = transaction_factory.create_realised_pnl_transaction(
        exchange_manager,
        currency=TRANSACTION_CURRENCY,
        symbol=TRANSACTION_SYMBOL,
        side=enums.PositionSide.LONG,
        realised_pnl=decimal.Decimal(0.1),
        closed_quantity=decimal.Decimal(1),
        cumulated_closed_quantity=decimal.Decimal(2),
        first_entry_time=decimal.Decimal(3),
        average_entry_price=decimal.Decimal(4),
        average_exit_price=decimal.Decimal(5),
        order_exit_price=decimal.Decimal(6),
        leverage=decimal.Decimal(7),
        trigger_source=enums.PNLTransactionSource.LIMIT_ORDER)
    assert transaction.currency == TRANSACTION_CURRENCY
    assert transaction.symbol == TRANSACTION_SYMBOL
    assert transaction.realised_pnl == decimal.Decimal(0.1)
    assert transaction.side is enums.PositionSide.LONG
    assert transaction.closed_quantity == decimal.Decimal(1)
    assert transaction.cumulated_closed_quantity == decimal.Decimal(2)
    assert transaction.first_entry_time == decimal.Decimal(3)
    assert transaction.average_entry_price == decimal.Decimal(4)
    assert transaction.average_exit_price == decimal.Decimal(5)
    assert transaction.order_exit_price == decimal.Decimal(6)
    assert transaction.leverage == decimal.Decimal(7)
    assert transaction.creation_time <= time.time()
    assert transaction.trigger_source is enums.PNLTransactionSource.LIMIT_ORDER
    assert len(exchange_manager.exchange_personal_data.transactions_manager.transactions) == 1


async def test_create_fee_transaction(backtesting_trader):
    _, exchange_manager, _ = backtesting_trader
    o_id = str(uuid.uuid4())
    transaction = transaction_factory.create_fee_transaction(exchange_manager,
                                                             currency=TRANSACTION_CURRENCY,
                                                             symbol=TRANSACTION_SYMBOL,
                                                             quantity=decimal.Decimal(10), order_id=o_id)
    assert transaction.currency == TRANSACTION_CURRENCY
    assert transaction.symbol == TRANSACTION_SYMBOL
    assert transaction.creation_time <= time.time()
    assert transaction.order_id == o_id
    assert transaction.transaction_id
    assert transaction.quantity == decimal.Decimal(10)
    assert len(exchange_manager.exchange_personal_data.transactions_manager.transactions) == 1


async def test_create_transfer_transaction(backtesting_trader):
    _, exchange_manager, _ = backtesting_trader
    transaction = transaction_factory.create_transfer_transaction(exchange_manager,
                                                                  currency=TRANSACTION_CURRENCY,
                                                                  symbol=TRANSACTION_SYMBOL)
    assert transaction.currency == TRANSACTION_CURRENCY
    assert transaction.symbol == TRANSACTION_SYMBOL
    assert transaction.creation_time <= time.time()
    assert len(exchange_manager.exchange_personal_data.transactions_manager.transactions) == 1
