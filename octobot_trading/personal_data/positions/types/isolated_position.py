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

import octobot_trading.constants as constants
import octobot_trading.personal_data.positions.position as position_class


class IsolatedPosition(position_class.Position):
    def update_liquidation_price(self):
        """
        Updates isolated position liquidation price
        LONG LIQUIDATION PRICE = (ENTRY_PRICE x LEVERAGE) / (LEVERAGE + 1 - (MAINTENANCE_MARGIN x LEVERAGE))
        SHORT LIQUIDATION PRICE = (ENTRY_PRICE x LEVERAGE) / (LEVERAGE - 1 + (MAINTENANCE_MARGIN x LEVERAGE))
        """
        try:
            if self.is_long():
                self.liquidation_price = (self.entry_price * self.leverage) / \
                                         (self.leverage + constants.ONE - (self.get_maintenance_margin() * self.leverage))
            elif self.is_short():
                self.liquidation_price = (self.entry_price * self.leverage) / \
                                         (self.leverage - constants.ONE + (self.get_maintenance_margin() * self.leverage))
            else:
                self.liquidation_price = constants.ZERO
            self._update_fee_to_close()
        except (decimal.DivisionByZero, decimal.InvalidOperation):
            self.liquidation_price = constants.ZERO
