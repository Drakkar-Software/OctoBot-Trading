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
import octobot_trading.storage as storage


def init_bot_storage(bot_id, config, tentacles_setup_config):
    if not storage.RunDatabasesProvider.instance().has_bot_id(bot_id):
        # only one run database per bot id
        storage.RunDatabasesProvider.instance().add_bot_id(bot_id, config, tentacles_setup_config)


def get_run_db(bot_id):
    return storage.RunDatabasesProvider.instance().get_run_db(bot_id)


def get_symbol_db(bot_id, exchange, symbol):
    return storage.RunDatabasesProvider.instance().get_symbol_db(bot_id, exchange, symbol)


async def close_bot_storage(bot_id):
    if storage.RunDatabasesProvider.instance().has_bot_id(bot_id):
        await storage.RunDatabasesProvider.instance().close(bot_id)
