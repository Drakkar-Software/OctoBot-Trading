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
import os
import json
import inspect
import hashlib
import contextlib

import octobot_commons.constants as common_constants
import octobot_commons.enums as common_enums
import octobot_commons.symbol_util as symbol_util
import octobot_commons.errors as common_errors
import octobot_commons.databases as databases
import octobot_commons.databases.adaptors as adaptors
import octobot_tentacles_manager.api as tentacles_manager_api
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

    def get_cache(self, tentacle_name=None):
        try:
            if tentacle_name is None:
                return self.tentacle.caches[self.symbol][self.time_frame]
            else:
                return self.trading_mode.remote_caches[tentacle_name][self.symbol][self.time_frame]
        except KeyError:
            if tentacle_name is None:
                if self.symbol not in self.tentacle.caches:
                    self.tentacle.caches[self.symbol] = {}
                # only the tentacle responsible for the cache is allowed to manage the actual database
                cache = self._open_or_create_cache_database(self.tentacle)
                self.tentacle.caches[self.symbol][self.time_frame] = cache
                tentacle_name = self.tentacle.get_name()
                # also register it in trading mode remote caches to share this instance later on
                if tentacle_name not in self.trading_mode.remote_caches:
                    self.trading_mode.remote_caches[tentacle_name] = {}
                if self.symbol not in self.trading_mode.remote_caches[tentacle_name]:
                    self.trading_mode.remote_caches[tentacle_name][self.symbol] = {}
                self.trading_mode.remote_caches[tentacle_name][self.symbol][self.time_frame] = cache
            else:
                try:
                    # always look into the trading mode remote caches only to ensure memory caches sync
                    cache = self.trading_mode.remote_caches[self.tentacle.get_name()][self.symbol][self.time_frame]
                except KeyError as e:
                    raise common_errors.NoCacheValue from e
            return cache

    def _open_or_create_cache_database(self, tentacle):
        cache_full_path = self.get_cache_path(tentacle)
        cache_dir = os.path.split(cache_full_path)[0]
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        return self._open_cache_database(cache_full_path)

    def has_cache(self, pair, time_frame):
        return pair in self.tentacle.caches and time_frame in self.tentacle.caches[pair]

    def get_cache_path(self, tentacle):
        try:
            if tentacle is self.tentacle:
                return self.tentacle.caches[self.symbol][self.time_frame].get_db_path()
            return self.tentacle.remote_caches[self.symbol][self.time_frame].get_db_path()
        except KeyError:
            # warning: very slow, should be called as rarely as possible
            return os.path.join(common_constants.USER_FOLDER, common_constants.CACHE_FOLDER, tentacle.get_name(),
                                self.exchange_name, self._sanitized_traded_pair, self.time_frame,
                                self._code_hash(tentacle), self._config_hash(tentacle), common_constants.CACHE_FILE)

    async def get_cached_value(self, value_key: str = common_enums.CacheDatabaseColumns.VALUE.value,
                               cache_key=None, tentacle_name=None):
        try:
            return await self.get_cache(tentacle_name=tentacle_name).\
                get(cache_key or self.trigger_cache_timestamp, name=value_key), False
        except common_errors.NoCacheValue:
            return None, True

    async def get_cached_values(self, value_key: str = common_enums.CacheDatabaseColumns.VALUE.value, cache_key=None,
                                limit=-1, tentacle_name=None) -> list:
        try:
            return await self.get_cache(tentacle_name=tentacle_name)\
                .get_values(cache_key or self.trigger_cache_timestamp, name=value_key, limit=limit)
        except common_errors.NoCacheValue:
            return []

    async def set_cached_value(self, value, value_key: str = common_enums.CacheDatabaseColumns.VALUE.value,
                               cache_key=None, flush_if_necessary=False, tentacle_name=None, **kwargs):
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

    @staticmethod
    def _code_hash(tentacle) -> str:
        code_location = tentacle.get_script() if hasattr(tentacle, "get_script") else tentacle.__class__
        return hashlib.sha256(
            inspect.getsource(code_location).replace(" ", "").replace("\n", "").encode()
        ).hexdigest()[:common_constants.CACHE_HASH_SIZE]

    def _config_hash(self, tentacle) -> str:
        config = tentacle.specific_config if hasattr(tentacle, "specific_config") else \
                 tentacles_manager_api.get_tentacle_config(self.exchange_manager.tentacles_setup_config,
                                                           tentacle.__class__)
        return hashlib.sha256(
            json.dumps(config).encode()
        ).hexdigest()[:common_constants.CACHE_HASH_SIZE]

    def _open_cache_database(self, file_path):
        """
        Override to use another cache database or adaptor
        :return: the cache database class
        """
        return databases.CacheTimestampDatabase(file_path, database_adaptor=databases.TinyDBAdaptor)

    @contextlib.asynccontextmanager
    async def run_data(self, with_lock=False, cache_size=None, database_adaptor=adaptors.TinyDBAdaptor):
        database_manager = databases.DatabaseManager(self.trading_mode.__class__,
                                                     database_adaptor=database_adaptor,
                                                     backtesting_id=self.backtesting_id,
                                                     optimizer_id=self.optimizer_id,
                                                     context=self)
        async with databases.MetaDatabase.database(database_manager, with_lock=with_lock,
                                                   cache_size=cache_size) as meta_db:
            yield meta_db
