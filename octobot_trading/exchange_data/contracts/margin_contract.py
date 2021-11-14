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
import octobot_trading.errors as errors


class MarginContract:
    def __init__(self, pair, margin_type,
                 contract_size=constants.ONE,
                 maximum_leverage=constants.ONE,
                 current_leverage=constants.ONE):
        self.pair = pair
        self.margin_type = margin_type

        self.contract_size = contract_size
        self.maximum_leverage = maximum_leverage
        self.current_leverage = current_leverage

        self.risk_limit = {}

    def is_isolated(self):
        """
        Margin in isolated margin mode is independent for each trading pair
        Margin in cross margin mode is shared among the user’s margin account
        :return: True if the contract use isolation margin
        """
        return self.margin_type is enums.MarginType.ISOLATED

    def set_current_leverage(self, new_leverage):
        """
        Set the contract current leverage value
        :param new_leverage: the new leverage value
        """
        if new_leverage <= self.maximum_leverage:
            self.current_leverage = new_leverage
        else:
            raise errors.InvalidLeverageValue(f"Trying to update leverage with {new_leverage} "
                                              f"but maximal value is {self.maximum_leverage}")

    def set_margin_type(self, is_isolated=True, is_cross=False):
        """
        Set the contract margin type
        :param is_isolated: should be True if the margin type is isolated
        :param is_cross: should be True if the margin type is cross
        """
        self.margin_type = enums.MarginType.ISOLATED if is_isolated and not is_cross else enums.MarginType.CROSS
