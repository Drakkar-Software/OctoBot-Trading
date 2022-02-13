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
import octobot_trading.enums as enums
import octobot_trading.constants as constants
import octobot_trading.personal_data.transactions.types as transaction_types


def create_blockchain_transaction(exchange_manager, currency,
                                  blockchain_type, blockchain_transaction_id,
                                  blockchain_transaction_status=enums.BlockchainTransactionStatus.CREATED,
                                  source_address=None, destination_address=None,
                                  quantity=constants.ZERO, transaction_fee=constants.ZERO, is_deposit=False):
    blockchain_transaction = transaction_types.BlockchainTransaction(
        exchange_name=exchange_manager.exchange_name,
        creation_time=exchange_manager.exchange.get_exchange_current_time(),
        transaction_type=enums.TransactionType.BLOCKCHAIN_DEPOSIT
        if is_deposit else enums.TransactionType.BLOCKCHAIN_WITHDRAWAL,
        currency=currency,
        blockchain_type=blockchain_type,
        blockchain_transaction_id=blockchain_transaction_id,
        blockchain_transaction_status=blockchain_transaction_status,
        source_address=source_address,
        destination_address=destination_address,
        quantity=quantity,
        transaction_fee=transaction_fee
    )
    _insert_transaction_instance(exchange_manager, blockchain_transaction)
    return blockchain_transaction


def create_realised_pnl_transaction(exchange_manager, currency, symbol, side,
                                    realised_pnl=constants.ZERO,
                                    is_closed_pnl=False,
                                    closed_quantity=constants.ZERO,
                                    cumulated_closed_quantity=constants.ZERO,
                                    first_entry_time=0,
                                    average_entry_price=constants.ZERO,
                                    average_exit_price=constants.ZERO,
                                    order_exit_price=constants.ZERO,
                                    leverage=constants.ZERO,
                                    trigger_source=enums.PNLTransactionSource.UNKNOWN):
    realised_pnl_transaction = transaction_types.RealisedPnlTransaction(
        exchange_name=exchange_manager.exchange_name,
        creation_time=exchange_manager.exchange.get_exchange_current_time(),
        transaction_type=enums.TransactionType.CLOSE_REALISED_PNL
        if is_closed_pnl else enums.TransactionType.REALISED_PNL,
        currency=currency,
        symbol=symbol,
        realised_pnl=realised_pnl,
        closed_quantity=closed_quantity,
        cumulated_closed_quantity=cumulated_closed_quantity,
        first_entry_time=first_entry_time,
        average_entry_price=average_entry_price,
        average_exit_price=average_exit_price,
        order_exit_price=order_exit_price,
        leverage=leverage,
        trigger_source=trigger_source,
        side=side)
    _insert_transaction_instance(exchange_manager, realised_pnl_transaction)
    return realised_pnl_transaction


def create_fee_transaction(exchange_manager, currency, symbol,
                           quantity=constants.ZERO,
                           order_id=None,
                           funding_rate=constants.ZERO):
    fee_transaction = transaction_types.FeeTransaction(
        exchange_name=exchange_manager.exchange_name,
        creation_time=exchange_manager.exchange.get_exchange_current_time(),
        transaction_type=enums.TransactionType.TRADING_FEE if order_id else enums.TransactionType.FUNDING_FEE,
        currency=currency,
        symbol=symbol,
        quantity=quantity,
        order_id=order_id,
        funding_rate=funding_rate)
    _insert_transaction_instance(exchange_manager, fee_transaction)
    return fee_transaction


def create_transfer_transaction(exchange_manager, currency, symbol):
    transfer_transaction = transaction_types.TransferTransaction(
        exchange_name=exchange_manager.exchange_name,
        creation_time=exchange_manager.exchange.get_exchange_current_time(),
        currency=currency,
        symbol=symbol)
    _insert_transaction_instance(exchange_manager, transfer_transaction)
    return transfer_transaction


def _insert_transaction_instance(exchange_manager, transaction):
    exchange_manager.exchange_personal_data.transactions_manager.insert_transaction_instance(transaction)
