# cython: language_level=3
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

cimport octobot_trading.personal_data.transactions.types as transaction_types

cpdef transaction_types.BlockchainTransaction create_blockchain_transaction(object exchange_manager,
                                                                            str currency,
                                                                            object blockchain_type,
                                                                            str blockchain_transaction_id,
                                                                            object blockchain_transaction_status=*,
                                                                            str source_address=*,
                                                                            str destination_address=*,
                                                                            object quantity=*,
                                                                            object transaction_fee=*,
                                                                            bint is_deposit=*)
cpdef transaction_types.RealisedPnlTransaction create_realised_pnl_transaction(object exchange_manager,
                                                                               str currency,
                                                                               str symbol,
                                                                               object realised_pnl=*,
                                                                               bint is_closed_pnl=*)
cpdef transaction_types.FeeTransaction create_fee_transaction(object exchange_manager,
                                                              str currency,
                                                              str symbol,
                                                              object quantity=*,
                                                              str order_id=*,
                                                              object funding_rate=*)
cpdef transaction_types.TransferTransaction create_transfer_transaction(object exchange_manager,
                                                                        str currency,
                                                                        str symbol)

cdef void _insert_transaction_instance(object exchange_manager, object transaction)
