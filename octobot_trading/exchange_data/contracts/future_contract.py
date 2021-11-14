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

import octobot_trading.exchange_data.contracts.margin_contract as margin_contract


class FutureContract(margin_contract.MarginContract):
    def __init__(self, pair, margin_type, contract_type,
                 contract_size=constants.ONE,
                 maximum_leverage=constants.ONE,
                 current_leverage=constants.ONE,
                 position_mode=enums.PositionMode.ONE_WAY,
                 minimum_tick_size=0.5):
        super().__init__(pair, margin_type=margin_type, contract_size=contract_size,
                         maximum_leverage=maximum_leverage, current_leverage=current_leverage)
        self.contract_type = contract_type
        self.minimum_tick_size = minimum_tick_size
        self.position_mode = position_mode

    def is_inverse_contract(self):
        """
        Inverse Contract is a contract using the coin itself as collateral
        if not inverted the contract uses fiat as the collateral
        :return: True if the contract is an inverse contract
        """
        return self.contract_type in [enums.FutureContractType.INVERSE_EXPIRABLE,
                                      enums.FutureContractType.INVERSE_PERPETUAL]

    def is_perpetual_contract(self):
        """
        Perpetual Contract is a contract without an expiry date
        :return: True if the contract is a perpetual contract
        """
        return self.contract_type in [enums.FutureContractType.LINEAR_PERPETUAL,
                                      enums.FutureContractType.INVERSE_PERPETUAL]

    def is_one_way_position_mode(self):
        """
        :return: True if the contract position_mode is equals to PositionMode's ONE_WAY
        """
        return self.position_mode is enums.PositionMode.ONE_WAY

    def set_position_mode(self, is_one_way=True, is_hedge=False):
        """
        Set the contract position mode
        :param is_one_way: should be True if the position mode is one way
        :param is_hedge: should be True if the position mode is hedge
        """
        self.position_mode = enums.PositionMode.ONE_WAY if is_one_way and not is_hedge else enums.PositionMode.HEDGE
