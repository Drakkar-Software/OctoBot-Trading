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
import asyncio
import os
import json
import inspect
import hashlib

import octobot_commons.constants as common_constants
import octobot_commons.enums as common_enums
import octobot_commons.symbol_util as symbol_util
import octobot_commons.errors as common_errors
import octobot_commons.databases as databases
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
        writer,
        trading_mode_class,
        trigger_cache_timestamp,
        trigger_source,
        trigger_value,
    ):
        self.tentacle = tentacle
        self.exchange_manager = exchange_manager
        self.trader = trader
        self.exchange_name = exchange_name
        self.traded_pair = traded_pair
        self.matrix_id = matrix_id
        self.cryptocurrency = cryptocurrency
        self.signal_symbol = signal_symbol
        self.time_frame = time_frame
        self.logger = logger
        self.writer = writer
        self.trading_mode_class = trading_mode_class
        self.trigger_cache_timestamp = trigger_cache_timestamp
        self.trigger_source = trigger_source
        self.trigger_value = trigger_value
        self._sanitized_traded_pair = symbol_util.merge_symbol(self.traded_pair) \
            if self.traded_pair else self.traded_pair
        # no cache if live trading to ensure cache is always writen
        self._flush_cache_when_necessary = not exchange_api.get_is_backtesting(exchange_manager) \
            if exchange_manager else False

    @staticmethod
    def minimal(trading_mode_class, logger):
        return Context(
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            logger,
            None,
            trading_mode_class,
            None,
            None,
            None
        )

    def get_cache(self):
        try:
            return self.tentacle.caches[self.traded_pair][self.time_frame]
        except KeyError:
            if self.traded_pair not in self.tentacle.caches:
                self.tentacle.caches[self.traded_pair] = {}
            cache_dir, cache_path = self.get_cache_path()
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            cache = self._get_cache_database(os.path.join(cache_dir, cache_path))
            self.tentacle.caches[self.traded_pair][self.time_frame] = cache
            return cache

    def has_cache(self, pair, time_frame):
        return pair in self.tentacle.caches and time_frame in self.tentacle.caches[pair]

    def get_cache_path(self):
        return os.path.join(common_constants.USER_FOLDER, common_constants.CACHE_FOLDER, self.tentacle.get_name(),
                            self.exchange_name, self._sanitized_traded_pair, self.time_frame,
                            self._code_hash(), self._config_hash()), common_constants.CACHE_FILE

    async def get_cached_value(self, value_key: str = common_enums.CacheDatabaseColumns.VALUE.value, cache_key=None):
        try:
            return await self.get_cache().get(cache_key or self.trigger_cache_timestamp, name=value_key), False
        except common_errors.NoCacheValue:
            return None, True

    async def set_cached_value(self, value, value_key: str = common_enums.CacheDatabaseColumns.VALUE.value,
                               cache_key=None, flush_if_necessary=False, **kwargs):
        cache = None
        try:
            cache = self.get_cache()
            await cache.set(cache_key or self.trigger_cache_timestamp, value, name=value_key)
            if kwargs:
                await asyncio.gather(*(
                    cache.set(cache_key or self.trigger_cache_timestamp, val,
                              name=f"{value_key}{common_constants.CACHE_RELATED_DATA_SEPARATOR}{key}")
                    for key, val in kwargs.items()
                ))
        finally:
            if flush_if_necessary and self._flush_cache_when_necessary and cache:
                await cache.flush()

    def _code_hash(self) -> str:
        code_location = self.tentacle.get_script() if hasattr(self.tentacle, "get_script") else self.tentacle.__class__
        return hashlib.sha256(
            inspect.getsource(code_location).replace(" ", "").replace("\n", "").encode()
        ).hexdigest()[:common_constants.CACHE_HASH_SIZE]

    def _config_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(tentacles_manager_api.get_tentacle_config(self.exchange_manager.tentacles_setup_config,
                                                                 self.tentacle.__class__)).encode()
        ).hexdigest()[:common_constants.CACHE_HASH_SIZE]

    def _get_cache_database(self, file_path):
        """
        Override to use another cache database or adaptor
        :return: the cache database class
        """
        return databases.CacheTimestampDatabase(file_path, database_adaptor=databases.TinyDBAdaptor)
