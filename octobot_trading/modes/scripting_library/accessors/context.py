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

import octobot_commons.constants as common_constants
import octobot_commons.symbol_util as symbol_util
import octobot_commons.databases as databases
import octobot_tentacles_manager.api as tentacles_manager_api


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
        return pair in self.tentacle.caches and time_frame in self.tentacle[pair]

    def get_cache_path(self):
        return os.path.join(common_constants.USER_FOLDER, common_constants.CACHE_FOLDER, self.tentacle.get_name(),
                            self.exchange_name, symbol_util.merge_symbol(self.traded_pair), self.time_frame,
                            self._code_hash(), self._config_hash()), common_constants.CACHE_FILE

    def _code_hash(self) -> str:
        return hashlib.sha256(
            inspect.getsource(self.tentacle.__class__).replace(" ", "").replace("\n", "").encode()
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
        import octobot_trading.api as exchange_api
        exchange_manager = exchange_api.get_exchange_manager_from_exchange_name_and_id(
            self.exchange_name,
            exchange_api.get_exchange_id_from_matrix_id(self.exchange_name, self.matrix_id)
        )
        # no cache if live trading to ensure cache is always writen
        cache_size = None if exchange_api.get_is_backtesting(exchange_manager) else 1
        return databases.CacheTimestampDatabase(file_path,
                                                database_adaptor=databases.TinyDBAdaptor,
                                                cache_size=cache_size)
