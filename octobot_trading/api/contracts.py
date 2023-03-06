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
import octobot_trading.exchange_data as exchange_data


def is_inverse_future_contract(contract_type):
    return exchange_data.FutureContract(None, None, contract_type).is_inverse_contract()


def is_perpetual_future_contract(contract_type):
    return exchange_data.FutureContract(None, None, contract_type).is_perpetual_contract()


def get_pair_contracts(exchange_manager) -> dict:
    return exchange_manager.exchange.pair_contracts


def is_handled_contract(contract) -> bool:
    return contract.is_handled_contract()
