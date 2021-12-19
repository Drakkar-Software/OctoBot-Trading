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

import octobot_commons.constants as common_constants
import octobot_commons.enums as common_enums
import octobot_commons.symbol_util as symbol_util
import octobot_commons.errors as common_errors
import octobot_commons.databases as databases
import octobot_trading.api as exchange_api


class Context:
    def __init__(
        self,
        tentacle,
        exchange_manager,
        trader,
        exchange_name,
        traded_pair,
        matrix_id,
        cryptocurrency,
        signal_symbol,
        time_frame,
        logger,
        run_data_writer,
        orders_writer,
        trades_writer,
        symbol_writer,
        trading_mode,
        trigger_cache_timestamp,
        trigger_source,
        trigger_value,
        backtesting_id,
        optimizer_id,
    ):
        self.tentacle = tentacle
        self.exchange_manager = exchange_manager
        self.trader = trader
        self.exchange_name = exchange_name
        self.symbol = traded_pair
        self.matrix_id = matrix_id
        self.cryptocurrency = cryptocurrency
        self.signal_symbol = signal_symbol
        self.time_frame = time_frame
        self.logger = logger
        self.run_data_writer = run_data_writer
        self.orders_writer = orders_writer
        self.trades_writer = trades_writer
        self.symbol_writer = symbol_writer
        self.trading_mode = trading_mode
        self.trigger_cache_timestamp = trigger_cache_timestamp
        self.trigger_source = trigger_source
        self.trigger_value = trigger_value
        self._sanitized_traded_pair = symbol_util.merge_symbol(self.symbol) \
            if self.symbol else self.symbol
        # no cache if live trading to ensure cache is always writen
        self._flush_cache_when_necessary = not exchange_api.get_is_backtesting(exchange_manager) \
            if exchange_manager else False
        self.backtesting_id = backtesting_id
        self.optimizer_id = optimizer_id
        self.allow_self_managed_orders = False
        self.plot_orders = False
        self.cache_manager = databases.CacheManager(database_adaptor=databases.TinyDBAdaptor)

    @staticmethod
    def minimal(trading_mode, logger, exchange_name, traded_pair, backtesting_id, optimizer_id):
        return Context(
            None,
            None,
            None,
            exchange_name,
            traded_pair,
            None,
            None,
            None,
            None,
            logger,
            None,
            None,
            None,
            None,
            trading_mode,
            None,
            None,
            None,
            backtesting_id,
            optimizer_id,
        )

    def get_cache(self, tentacle_name=None, cache_type=databases.CacheTimestampDatabase):
        tentacle = self.tentacle if tentacle_name is None else None
        tentacle_name = tentacle_name or self.tentacle.get_name()
        return self.cache_manager.get_cache(tentacle, tentacle_name, self.exchange_name, self.symbol, self.time_frame,
                                            self.exchange_manager.tentacles_setup_config,
                                            cache_type=cache_type)

    def has_cache(self, pair, time_frame):
        return self.cache_manager.has_cache(self.tentacle.get_name(), self.exchange_name, pair, time_frame)

    def get_cache_path(self, tentacle):
        return self.cache_manager.get_cache_path(tentacle, self.exchange_name, self.symbol, self.time_frame,
                                                 tentacle.get_name(), self.exchange_manager.tentacles_setup_config)

    async def get_cached_value(self,
                               value_key: str = common_enums.CacheDatabaseColumns.VALUE.value,
                               cache_key=None,
                               tentacle_name=None) -> tuple:
        """
        Get a value for the current cache
        :param value_key: identifier of the value
        :param cache_key: timestamp to use in order to look for a value
        :param tentacle_name: name of the tentacle to get cache from
        :return: the cached value and a boolean (True if cached value is missing from cache)
        """
        try:
            return await self.get_cache(tentacle_name=tentacle_name).\
                get(cache_key or self.trigger_cache_timestamp, name=value_key), False
        except common_errors.NoCacheValue:
            return None, True

    async def get_cached_values(self,
                                value_key: str = common_enums.CacheDatabaseColumns.VALUE.value,
                                cache_key=None,
                                limit=-1,
                                tentacle_name=None) -> list:
        """
        Get a value for the current cache
        :param value_key: identifier of the value
        :param cache_key: timestamp to use in order to look for a value
        :param limit: the maximum number elements to select (no limit by default)
        :param tentacle_name: name of the tentacle to get cache from
        :return: the cached values
        """
        try:
            return await self.get_cache(tentacle_name=tentacle_name)\
                .get_values(cache_key or self.trigger_cache_timestamp, name=value_key, limit=limit)
        except common_errors.NoCacheValue:
            return []

    async def set_cached_value(self, value, value_key: str = common_enums.CacheDatabaseColumns.VALUE.value,
                               cache_key=None, flush_if_necessary=False, tentacle_name=None, **kwargs):
        """
        Set a value into the current cache
        :param value: value to set
        :param value_key: identifier of the value
        :param cache_key: timestamp to associate the value to
        :param flush_if_necessary: flush the cache after set (write into database)
        :param tentacle_name: name of the tentacle to get cache from
        :param kwargs: other related value_key / value couples to set at this timestamp. Use for plotted data
        :return: None
        """
        cache = None
        try:
            cache = self.get_cache(tentacle_name=tentacle_name)
            await cache.set(cache_key or self.trigger_cache_timestamp, value, name=value_key)
            if kwargs:
                for key, val in kwargs.items():
                    await cache.set(
                        cache_key or self.trigger_cache_timestamp,
                        val,
                        name=f"{value_key}{common_constants.CACHE_RELATED_DATA_SEPARATOR}{key}"
                    )
        finally:
            if flush_if_necessary and self._flush_cache_when_necessary and cache:
                await cache.flush()

    @contextlib.asynccontextmanager
    async def run_data(self, with_lock=False, cache_size=None, database_adaptor=databases.TinyDBAdaptor):
        database_manager = databases.DatabaseManager(self.trading_mode.__class__,
                                                     database_adaptor=database_adaptor,
                                                     backtesting_id=self.backtesting_id,
                                                     optimizer_id=self.optimizer_id,
                                                     context=self)
        async with databases.MetaDatabase.database(database_manager, with_lock=with_lock,
                                                   cache_size=cache_size) as meta_db:
            yield meta_db
