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
import octobot_commons.databases as databases


class BaseDatabase:
    def __init__(self, file_path: str, database_adaptor=databases.TinyDBAdaptor):
        self._database = databases.DocumentDatabase(database_adaptor(file_path))
        self.are_data_initialized = False

    def search(self):
        return self._database.query_factory()

    def count(self, table_name: str, query) -> int:
        return self._database.count(table_name, query)

    def close(self):
        self._database.close()
