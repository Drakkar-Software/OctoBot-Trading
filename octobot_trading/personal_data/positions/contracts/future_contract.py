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


class FutureContract:
    def __init__(self, pair):
        self.pair = pair

        self.contract_type = enums.FutureContractType.INVERSE_PERPETUAL
        self.margin_type = enums.MarginType.ISOLATED
        self.expiration_timestamp = 0

        self.minimum_tick_size = 0.5
        self.contract_size = constants.ONE
        self.maximum_leverage = constants.ONE
        self.current_leverage = constants.ONE

    def is_inverse_contract(self):
        """
        :return: True if the contract is an inverse contract
        """
        return self.contract_type in [enums.FutureContractType.INVERSE_EXPIRABLE,
                                      enums.FutureContractType.INVERSE_PERPETUAL]

    def is_isolated(self):
        """
        :return: True if the contract use isolation margin
        """
        return self.margin_type is enums.MarginType.ISOLATED
