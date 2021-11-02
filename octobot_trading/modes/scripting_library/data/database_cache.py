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
import octobot_trading.enums as trading_enums


class DatabaseCache:

    def __init__(self):
        self.cache = {}

    def register(self, table, row):
        try:
            self.cache[table].append(row)
        except KeyError:
            self.cache[table] = [row]

    def has(self, table):
        return table in self.cache

    def contains_x(self, table, x_val):
        try:
            for element in self.cache[table]:
                if element["x"] == x_val:
                    return True
        except KeyError:
            pass
        return False
