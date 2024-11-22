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
import decimal

import octobot_trading.enums as enums
import octobot_trading.exchange_data as exchange_data

def is_inverse_future_contract(contract_type):
    return exchange_data.FutureContract(None, None, contract_type).is_inverse_contract()


def is_perpetual_future_contract(contract_type):
    return exchange_data.FutureContract(None, None, contract_type).is_perpetual_contract()


def get_pair_contracts(exchange_manager) -> dict:
    return exchange_manager.exchange.pair_contracts


def is_handled_contract(contract) -> bool:
    return contract.is_handled_contract()


def has_pair_future_contract(exchange_manager, pair: str) -> bool:
    return exchange_manager.exchange.has_pair_future_contract(pair)


def load_pair_contract(exchange_manager, contract_dict: dict):
    exchange_data.update_future_contract_from_dict(exchange_manager, contract_dict)


def create_default_future_contract(
    pair: str, leverage: decimal.Decimal, contract_type: enums.FutureContractType
) -> exchange_data.FutureContract:
    return exchange_data.create_default_future_contract(pair, leverage, contract_type)
