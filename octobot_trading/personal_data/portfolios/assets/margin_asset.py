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
import octobot_trading.personal_data.portfolios.asset as asset_class
import octobot_trading.constants as constants


class MarginAsset(asset_class.Asset):
    def __init__(self, name, available, total):
        super().__init__(name, available, total)
        self.borrowed = constants.ZERO
        self.interest = constants.ZERO
        self.locked = constants.ZERO

    def __eq__(self, other):
        if isinstance(other, MarginAsset):
            return self.available == other.available and self.total == other.total and self.borrowed == other.borrowed
        return False
