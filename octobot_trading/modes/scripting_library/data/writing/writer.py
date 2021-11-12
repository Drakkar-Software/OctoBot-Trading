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
import octobot_trading.modes.scripting_library.data as database


class DBWriter(database.BaseDatabase):

    async def log(self, table_name: str, row: dict, cache_only=False):
        self.cache.register(table_name, row)
        if not cache_only:
            await self._database.insert(table_name, row)

    async def update(self, table_name: str, row: dict, query):
        await self._database.update(table_name, row, query)

    async def delete(self, table_name: str, query):
        await self._database.delete(table_name, query)

    async def log_many(self, table_name: str, rows: list, cache_only=False):
        for row in rows:
            self.cache.register(table_name, row)
        if not cache_only:
            await self._database.insert_many(table_name, rows)

    async def flush_cache(self):
        for table, rows in self.cache.cache.items():
            await self._database.insert_many(table, rows)
        self.cache = {}

    @staticmethod
    def get_value_from_array(array, index, multiplier=1):
        if array is None:
            return None
        return array[index] * multiplier
