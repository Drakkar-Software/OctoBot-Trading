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

import octobot_trading.exchange_data.contracts.margin_contract as margin_contract


class FutureContract(margin_contract.MarginContract):
    def __init__(self, pair):
        super().__init__(pair)
        self.contract_type = None

        self.creation_date = 0
        self.expiration_date = 0

        self.minimum_tick_size = 0.5

    def is_inverse_contract(self):
        """
        Inverse Contract is a contract using the coin itself as collateral
        if not inverted the contract uses fiat as the collateral
        :return: True if the contract is an inverse contract
        """
        return self.contract_type in [enums.FutureContractType.INVERSE_EXPIRABLE,
                                      enums.FutureContractType.INVERSE_PERPETUAL]
