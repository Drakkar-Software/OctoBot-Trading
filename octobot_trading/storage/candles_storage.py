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
#  License along with this library
import asyncio

import octobot_commons.enums as commons_enums
import octobot_commons.constants as commons_constants
import octobot_commons.databases as commons_databases

import octobot_backtesting.api as backtesting_api
import octobot_trading.storage.abstract_storage as abstract_storage
import octobot_trading.util as util


class CandlesStorage(abstract_storage.AbstractStorage):
    IS_LIVE_CONSUMER = False
    IS_HISTORICAL = False
    HISTORY_TABLE = commons_enums.DBTables.CANDLES_SOURCE.value

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_task = None
        self._init_timeout = 5 * commons_constants.MINUTE_TO_SECONDS

    async def on_start(self):
        self._init_task = asyncio.create_task(self._store_candles_when_available())

    async def stop(self, **kwargs):
        if self._init_task is not None and not self._init_task.done():
            self._init_task.cancel()
        await super().stop(**kwargs)

    async def _store_candles_when_available(self):
        await util.wait_for_topic_init(self.exchange_manager, self._init_timeout,
                                       commons_enums.InitializationEventExchangeTopics.CANDLES.value)
        await self.store_candles()

    async def store_candles(self):
        if not self.enabled:
            return
        for symbol in self.exchange_manager.exchange_config.traded_symbol_pairs:
            symbol_db = self._get_db(symbol)
            for time_frame in self.exchange_manager.exchange_config.get_relevant_time_frames():
                await symbol_db.delete(self.HISTORY_TABLE, None)
                await self._store_candles_if_necessary(symbol, time_frame.value, symbol_db)

    async def _store_candles_if_necessary(self, symbol, time_frame, symbol_db):
        candles_data = {
            "time_frame": time_frame,
            "value": backtesting_api.get_data_file_from_importers(
                self.exchange_manager.exchange.connector.exchange_importers, symbol,
                commons_enums.TimeFrames(time_frame)
            )
            if self.exchange_manager.is_backtesting else commons_constants.LOCAL_BOT_DATA,
            "chart": self.plot_settings.chart
        }
        if (not await symbol_db.contains_row(
                self.HISTORY_TABLE,
                {
                    "time_frame": time_frame,
                    "value": candles_data["value"],
                })):
            await symbol_db.log(self.HISTORY_TABLE, candles_data)

    async def clear_history(self, flush=True):
        for database in await self._get_all_symbol_dbs():
            await database.delete(self.HISTORY_TABLE, None)
            if flush:
                await database.flush()

    def _get_db(self, symbol):
        return commons_databases.RunDatabasesProvider.instance().get_symbol_db(
            self.exchange_manager.bot_id,
            self.exchange_manager.exchange_name,
            symbol
        )

    async def _get_all_symbol_dbs(self):
        return await commons_databases.RunDatabasesProvider.instance().get_all_symbol_dbs(
            self.exchange_manager.bot_id,
            self.exchange_manager.exchange_name
        )

