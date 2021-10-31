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
import numpy
import octobot_trading.modes.scripting_library.data.database as database


class DBWriter(database.BaseDatabase):

    def log(self, table_name: str, row: dict):
        self._database.insert(table_name, row)

    def update(self, table_name: str, row: dict, query):
        self._database.update(table_name, row, query)

    def log_many(self, table_name: str, rows: list):
        self._database.insert_many(table_name, rows)

    @staticmethod
    def get_value_from_array(array, index, multiplier=1):
        if array is None:
            return None
        return array[index] * multiplier

    @staticmethod
    def get_serializable_value(value):
        return value.item() if isinstance(value, numpy.generic) else value
