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
import octobot_trading.modes.scripting_library.data.database as database


class DBReader(database.BaseDatabase):
    async def select(self, table_name: str, query: str) -> list:
        return await self._database.select(table_name, query)

    async def tables(self) -> list:
        return await self._database.tables()

    async def all(self, table_name: str) -> list:
        return await self._database.select(table_name, None)
