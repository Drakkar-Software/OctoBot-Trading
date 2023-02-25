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
import octobot_commons.logging as logging

import octobot_trading.enums as enums
import octobot_trading.constants as constants


def update_contracts_from_positions(exchange_manager, positions) -> bool:
    updated = False
    for position in positions:
        pair = position.get(enums.ExchangeConstantsPositionColumns.SYMBOL.value, None)
        if pair and pair not in exchange_manager.exchange.pair_contracts:
            contract = exchange_manager.exchange.create_pair_contract(
                pair=pair,
                current_leverage=position.get(
                    enums.ExchangeConstantsPositionColumns.LEVERAGE.value, constants.ZERO),
                contract_size=position.get(
                    enums.ExchangeConstantsPositionColumns.CONTRACT_SIZE.value, constants.DEFAULT_SYMBOL_CONTRACT_SIZE),
                margin_type=position.get(enums.ExchangeConstantsPositionColumns.MARGIN_TYPE.value, None),
                contract_type=position.get(enums.ExchangeConstantsPositionColumns.CONTRACT_TYPE.value, None),
                position_mode=position.get(enums.ExchangeConstantsPositionColumns.POSITION_MODE.value, None),
                maintenance_margin_rate=position.get(
                    enums.ExchangeConstantsPositionColumns.MAINTENANCE_MARGIN_RATE.value,
                    constants.DEFAULT_SYMBOL_MAINTENANCE_MARGIN_RATE)
            )
            # contracts are updated from positions are fully initialized
            if contract.is_handled_contract():
                updated = True
            else:
                message = f"Unhandled contract {contract}. This contract can't be traded"
                if pair in exchange_manager.exchange_config.traded_symbol_pairs:
                    # inform user that the contract can't be used
                    _get_logger().error(message)
                else:
                    # no need to inform as the contract is not requested
                    _get_logger().debug(message)
    return updated


def _get_logger():
    return logging.get_logger("contract_factory")
