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
import octobot_commons.singleton as singleton
import octobot_commons.databases as databases
import octobot_commons.errors as errors
import octobot_trading.util as util


class RunDatabasesProvider(singleton.Singleton):
    def __init__(self):
        self.run_databases = {}

    def add_bot_id(self, bot_id, config, tentacles_setup_config, with_lock=False, cache_size=None):
        run_dbs_identifier = util.get_run_databases_identifier(config, tentacles_setup_config)
        self.run_databases[bot_id] = databases.MetaDatabase(run_dbs_identifier, with_lock=with_lock,
                                                            cache_size=cache_size)

    def has_bot_id(self, bot_id):
        return bot_id in self.run_databases

    def get_run_databases_identifier(self, bot_id):
        return self.run_databases[bot_id].run_dbs_identifier

    def get_run_db(self, bot_id):
        return self.run_databases[bot_id].get_run_db()

    def get_orders_db(self, bot_id, exchange=None):
        return self.run_databases[bot_id].get_orders_db(exchange=exchange)

    def get_trades_db(self, bot_id, exchange=None):
        return self.run_databases[bot_id].get_trades_db(exchange=exchange)

    def get_transactions_db(self, bot_id, exchange=None):
        return self.run_databases[bot_id].get_transactions_db(exchange=exchange)

    def get_backtesting_metadata_db(self, bot_id):
        return self.run_databases[bot_id].get_backtesting_metadata_db()

    def get_symbol_db(self, bot_id, exchange, symbol):
        if not symbol:
            raise errors.DatabaseNotFoundError("symbol parameter has to be provided")
        return self.run_databases[bot_id].get_symbol_db(exchange, symbol)

    async def close(self, bot_id):
        await self.run_databases[bot_id].close()
        self.run_databases.pop(bot_id)
