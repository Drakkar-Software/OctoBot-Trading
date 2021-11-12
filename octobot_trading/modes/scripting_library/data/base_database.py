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
import contextlib
import numpy

import octobot_commons.databases as databases
import octobot_trading.modes.scripting_library.data as data


class BaseDatabase:
    def __init__(self, file_path: str, database_adaptor=databases.TinyDBAdaptor):
        self._database = databases.DocumentDatabase(database_adaptor(file_path))
        self.are_data_initialized = False
        self.cache = data.DatabaseCache()

    def get_db_path(self):
        return self._database.get_db_path()

    async def search(self):
        return await self._database.query_factory()

    async def count(self, table_name: str, query) -> int:
        return await self._database.count(table_name, query)

    async def close(self):
        await self.flush_cache()
        await self._database.close()

    def contains_x(self, table: str, x_val):
        return self.cache.contains_x(table, x_val)

    def contains_values(self, table: str, val_by_keys: dict):
        return self.cache.contains_values(table, val_by_keys)

    async def flush_cache(self):
        pass

    @classmethod
    @contextlib.asynccontextmanager
    async def database(cls, *args, **kwargs):
        database = None
        try:
            database = cls(*args, **kwargs)
            yield database
        finally:
            if database is not None:
                await database.close()

    @staticmethod
    def get_serializable_value(value):
        return value.item() if isinstance(value, numpy.generic) else value
