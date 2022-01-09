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
import copy

import octobot_commons.constants as common_constants
import octobot_commons.enums as common_enums
import octobot_commons.symbol_util as symbol_util
import octobot_commons.errors as common_errors
import octobot_commons.databases as databases
import octobot_commons.display as commons_display
import octobot_commons.tentacles_management as tentacles_management
import octobot_backtesting.api as backtesting_api
import octobot_trading.modes as modes


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
        self._flush_cache_when_necessary = not exchange_manager.is_backtesting if exchange_manager else False
        self.backtesting_id = backtesting_id
        self.optimizer_id = optimizer_id
        self.allow_self_managed_orders = False
        self.plot_orders = False
        self.cache_manager = databases.CacheManager(database_adaptor=databases.TinyDBAdaptor)
        self.just_created_orders = []

        # nested calls management
        self.config_name = None
        self.top_level_tentacle = tentacle
        self.is_nested_tentacle = False
        self.nested_depth = 0
        self.nested_config_names = []
        self.tentacles_requirements = tentacles_management.TentacleRequirements(self.tentacle, self.config_name)
        self.parent_tentacles_requirements = None

    @contextlib.contextmanager
    def adapted_trigger_timestamp(self, tentacle_class, config_name):
        previous_trigger_cache_timestamp = self.trigger_cache_timestamp
        try:
            if isinstance(self.tentacle, modes.AbstractTradingMode) and \
                    self.trigger_source == common_enums.ActivationTopics.EVALUATORS.value:
                # only trading modes can have a delayed trigger timestamp when they are waken up from evaluators
                self.trigger_cache_timestamp = self._get_adapted_trigger_timestamp(tentacle_class,
                                                                                   previous_trigger_cache_timestamp,
                                                                                   config_name)
            yield self
        finally:
            self.trigger_cache_timestamp = previous_trigger_cache_timestamp

    @contextlib.asynccontextmanager
    async def local_nested_tentacle_config(self, tentacle_class, config_name, is_nested_tentacle):
        previous_is_nested_tentacle = self.is_nested_tentacle
        previous_config_name = self.config_name
        previous_parent_tentacles_requirements = self.parent_tentacles_requirements
        previous_tentacle_requirements = self.tentacles_requirements
        try:
            self.is_nested_tentacle = is_nested_tentacle
            self.config_name = config_name
            self.nested_depth += 1
            self.nested_config_names.append(config_name)
            self.parent_tentacles_requirements = self.tentacles_requirements
            # self.tentacles_requirements.get_requirement might return None on the 1st call,
            # it will be populated during this first call
            self.tentacles_requirements = self.tentacles_requirements.get_requirement(tentacle_class, config_name)
            yield self
        finally:
            self.is_nested_tentacle = previous_is_nested_tentacle
            self.config_name = previous_config_name
            self.parent_tentacles_requirements = previous_parent_tentacles_requirements
            self.tentacles_requirements = previous_tentacle_requirements
            self.nested_depth -= 1
            del self.nested_config_names[-1]
            if self._requires_cache_sync_synchronization():
                # if tentacles requirements changed: reset cache of this tentacle to include the new requirements
                await self._reset_cache()

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

    def get_nested_call_context(self, tentacle):
        context = Context(
            tentacle,
            self.exchange_manager,
            self.trader,
            self.exchange_name,
            self.symbol,
            self.matrix_id,
            self.cryptocurrency,
            self.signal_symbol,
            self.time_frame,
            self.logger,
            self.run_data_writer,
            self.orders_writer,
            self.trades_writer,
            self.symbol_writer,
            self.trading_mode,
            self.trigger_cache_timestamp,
            self.trigger_source,
            self.trigger_value,
            self.backtesting_id,
            self.optimizer_id
        )
        context.is_nested_tentacle = self.is_nested_tentacle
        context.config_name = self.config_name
        context.nested_depth = self.nested_depth
        context.nested_config_names = copy.copy(self.nested_config_names)
        # always keep top level tentacle
        context.top_level_tentacle = self.top_level_tentacle
        context.tentacles_requirements = self.tentacles_requirements  # keep the same tentacles_requirements
        context.parent_tentacles_requirements = self.parent_tentacles_requirements
        context.add_tentacle_requirement_from_nested_context(tentacle, context.config_name)
        return context

    def add_tentacle_requirement_from_nested_context(self, tentacle, config_name) \
            -> (bool, tentacles_management.TentacleRequirements):
        """
        Used to add a requirement to a tentacle that has been triggered. Allows initialise its cache.
        Updates self.tentacles_requirements and self.parent_tentacles_requirements
        :param tentacle: the required tentacle tentacle
        :param config_name: its configuration name
        :return True if the requirement was not already registered and the created requirement
        """
        # self.tentacles_requirements might be None during the 1st nested call as it is retrieved from
        # the parent context. At 1st call, it has not yet been initialized
        if self.tentacles_requirements is None:
            self.tentacles_requirements = tentacles_management.TentacleRequirements(tentacle, config_name)
        return self.parent_tentacles_requirements.add_requirement(self.tentacles_requirements), \
            self.tentacles_requirements

    def add_referenced_tentacle_requirement(self, tentacle_class, config_name) \
            -> (bool, tentacles_management.TentacleRequirements):
        """
        Used to add a requirement to a tentacle that was already triggered. Does not allow to initialise its cache.
        Only updates self.tentacles_requirements.
        Does not update self.parent_tentacles_requirements is it should already contain a reference to
        self.tentacles_requirements from the previous trigger. Even if it was called, resetting its cache would fail
        because there is no available tentacle instance to get its configuration from (only a class is available).
        Set the return requirement tentacle attribute to allow cache initialization
        :param tentacle_class: the required tentacle class
        :param config_name: its configuration name
        :return True if the requirement was not already registered and the created requirement
        """
        requirement = tentacles_management.TentacleRequirements(None, config_name, tentacle_class=tentacle_class)
        return self.tentacles_requirements.add_requirement(requirement), requirement

    def _get_adapted_trigger_timestamp(self, tentacle_class, base_trigger_timestamp, config_name):
        try:
            if self.has_cache(self.symbol, self.time_frame, tentacle_name=tentacle_class.get_name(),
                              config_name=config_name):
                cache = self.get_cache(tentacle_name=tentacle_class.get_name(), config_name=config_name)
                if cache.metadata.get(common_enums.CacheDatabaseColumns.TRIGGERED_AFTER_CANDLES_CLOSE.value, False):
                    return base_trigger_timestamp - \
                           common_enums.TimeFramesMinutes[common_enums.TimeFrames(self.time_frame)] * \
                           common_constants.MINUTE_TO_SECONDS
            return base_trigger_timestamp
        except common_errors.NoCacheValue:
            # should not happen
            raise

    def get_cache_registered_requirements(self, tentacle_name=None, config_name=None):
        try:
            return self.cache_manager.get_cache_registered_requirements(
                tentacle_name or self.tentacle.get_name(),
                self.exchange_name,
                self.symbol,
                self.time_frame,
                config_name or self.config_name
            )
        except KeyError:
            return None

    async def ensure_nested_call_cache_requirements(self, tentacle_class, config_name):
        """
        Takes into account a tentacle and its config_name to identify cache.
        Requires the given tentacle to have been called previously as this method is not
        initializing this tentacle cache but only binding to it
        """
        added, requirement = self.add_referenced_tentacle_requirement(tentacle_class, config_name)
        if added and self._requires_cache_sync_synchronization():
            # build a new tentacle instance with appropriate config (from previous trigger) to use it as requirement
            config_name, _, _, tentacles_setup_config, _ = \
                self.get_tentacle_config_elements(tentacle_class, config_name, None)
            # use already registered requirement to access its configuration (config might be updated during script run)
            registered_requirement = self.get_cache_registered_requirements(tentacle_class.get_name(), config_name)
            requirement.tentacle = tentacle_class.factory_with_local_config(tentacles_setup_config,
                                                                            registered_requirement.tentacle_config)
            await self._reset_cache()

    def get_tentacle_config_elements(self, tentacle_class, config_name, config):
        config_name = f"nested_{tentacle_class.get_name()}_config" if config_name is None else config_name
        cleaned_config_name = config_name.replace(" ", "_")
        config = {key.replace(" ", "_"): val for key, val in config.items()} if config else {}
        tentacles_setup_config = self.tentacle.tentacles_setup_config \
            if hasattr(self.tentacle, "tentacles_setup_config") else self.exchange_manager.tentacles_setup_config
        tentacle_config = self.tentacle.specific_config if hasattr(self.tentacle, "specific_config") \
            else self.tentacle.trading_config
        return config_name, cleaned_config_name, config, tentacles_setup_config, tentacle_config

    def _requires_cache_sync_synchronization(self):
        registered_requirements = self.get_cache_registered_requirements()
        return registered_requirements is not None and not registered_requirements.includes_nested_requirements(
                self.tentacles_requirements
        )

    async def _reset_cache(self):
        previous_cache_requirements = self.get_cache_registered_requirements()
        await self.cache_manager.reset_cache(
            self.tentacle.get_name(), self.exchange_name, self.symbol, self.time_frame, self.config_name
        )
        self.init_cache()
        self.logger.debug(f"Replaced cache for {self.tentacle.get_name()} ({self.config_name}) to include "
                          f"{self.get_cache_registered_requirements()} requirements (previously was "
                          f"{previous_cache_requirements}")

    def get_cache(self, tentacle_name=None, cache_type=databases.CacheTimestampDatabase, config_name=None):
        tentacle = self.tentacle if tentacle_name is None else None
        tentacle_name = tentacle_name or self.tentacle.get_name()
        config_name = config_name or self.config_name
        cache, just_created = self.cache_manager.get_cache(
            tentacle, tentacle_name, self.exchange_name, self.symbol, self.time_frame, config_name,
            self.exchange_manager.tentacles_setup_config, self.tentacles_requirements, cache_type=cache_type
        )
        if just_created and cache_type is databases.CacheTimestampDatabase:
            metadata = self.cache_manager.get_cache_previous_db_metadata(
                tentacle_name, self.exchange_name, self.symbol, self.time_frame, config_name)
            if tentacle is None:
                metadata = self.cache_manager.get_cache_previous_db_metadata(
                    tentacle_name, self.exchange_name, self.symbol, self.time_frame, config_name)
            else:
                metadata = {
                    common_enums.CacheDatabaseColumns.TRIGGERED_AFTER_CANDLES_CLOSE.value:
                        tentacle.is_triggered_after_candle_close
                }
            if metadata is None:
                raise RuntimeError(f"Missing db metadata. Please provide the tentacle parameter to this method")
            cache.add_metadata(metadata)
        return cache

    def has_cache(self, pair, time_frame, tentacle_name=None, config_name=None):
        config_name = config_name or self.config_name
        return self.cache_manager.has_cache(tentacle_name or self.tentacle.get_name(), self.exchange_name,
                                            pair, time_frame, config_name)

    def get_cache_path(self, tentacle, config_name=None):
        config_name = config_name or self.config_name
        return self.cache_manager.get_cache_or_build_path(
            tentacle, self.exchange_name, self.symbol, self.time_frame, tentacle.get_name(), config_name,
            self.exchange_manager.tentacles_setup_config, self.tentacles_requirements
        )

    def init_cache(self):
        self.get_cache()

    async def get_cached_value(self,
                               value_key: str = common_enums.CacheDatabaseColumns.VALUE.value,
                               cache_key=None,
                               tentacle_name=None,
                               config_name=None) -> tuple:
        """
        Get a value for the current cache
        :param value_key: identifier of the value
        :param cache_key: timestamp to use in order to look for a value
        :param tentacle_name: name of the tentacle to get cache from
        :param config_name: name of the tentacle configuration as used in nested tentacle calls
        :return: the cached value and a boolean (True if cached value is missing from cache)
        """
        try:
            return await self.get_cache(tentacle_name=tentacle_name, config_name=config_name).\
                get(cache_key or self.trigger_cache_timestamp, name=value_key), False
        except common_errors.NoCacheValue:
            return None, True

    async def get_cached_values(self,
                                value_key: str = common_enums.CacheDatabaseColumns.VALUE.value,
                                cache_key=None,
                                limit=-1,
                                tentacle_name=None,
                                config_name=None,
                                bound_to_backtesting_time=True) -> list:
        """
        Get a value for the current cache with the current backtesting boundaries
        :param value_key: identifier of the value
        :param cache_key: timestamp to use in order to look for a value
        :param limit: the maximum number elements to select (no limit by default)
        :param tentacle_name: name of the tentacle to get cache from
        :param config_name: name of the tentacle configuration as used in nested tentacle calls
        :param bound_to_backtesting_time: only select cache from values within the current total backtesting time window
        :return: the cached values
        """
        try:
            min_timestamp = 0
            max_timestamp = cache_key or self.trigger_cache_timestamp
            if bound_to_backtesting_time and self.exchange_manager.is_backtesting:
                min_timestamp = backtesting_api.get_backtesting_starting_time(
                    self.exchange_manager.exchange.backtesting)
                max_timestamp = min(cache_key or self.trigger_cache_timestamp,
                                    backtesting_api.get_backtesting_ending_time(
                                        self.exchange_manager.exchange.backtesting))
            return await self.get_cache(tentacle_name=tentacle_name, config_name=config_name)\
                .get_values(max_timestamp, name=value_key, limit=limit,
                            min_timestamp=min_timestamp)
        except common_errors.NoCacheValue:
            return []

    async def set_cached_value(self, value, value_key: str = common_enums.CacheDatabaseColumns.VALUE.value,
                               cache_key=None, flush_if_necessary=False, tentacle_name=None, config_name=None,
                               **kwargs):
        """
        Set a value into the current cache
        :param value: value to set
        :param value_key: identifier of the value
        :param cache_key: timestamp to associate the value to
        :param flush_if_necessary: flush the cache after set (write into database)
        :param tentacle_name: name of the tentacle to get cache from
        :param config_name: name of the tentacle configuration as used in nested tentacle calls
        :param kwargs: other related value_key / value couples to set at this timestamp. Use for plotted data
        :return: None
        """
        cache = None
        try:
            cache = self.get_cache(tentacle_name=tentacle_name, config_name=config_name)
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

    async def set_cached_values(self, values, value_key, cache_keys, flush_if_necessary=False, tentacle_name=None,
                                config_name=None, additional_values_by_key=None):
        """
        Set a value into the current cache
        :param values: values to set
        :param value_key: identifier of the value
        :param cache_keys: timestamps to associate the values to
        :param flush_if_necessary: flush the cache after set (write into database)
        :param tentacle_name: name of the tentacle to get cache from
        :param config_name: name of the tentacle configuration as used in nested tentacle calls
        :param additional_values_by_key: other values to set in a dict of cache_keys
        :return: None
        """
        cache = None
        try:
            cache = self.get_cache(tentacle_name=tentacle_name, config_name=config_name)
            await cache.set_values(cache_keys, values, name=value_key,
                                   additional_values_by_key=additional_values_by_key)
        finally:
            if flush_if_necessary and self._flush_cache_when_necessary and cache:
                await cache.flush()

    @contextlib.asynccontextmanager
    async def backtesting_results(self, with_lock=False, cache_size=None, database_adaptor=databases.TinyDBAdaptor):
        display = commons_display.display_translator_factory()
        database_manager = databases.DatabaseManager(self.trading_mode.__class__,
                                                     database_adaptor=database_adaptor,
                                                     backtesting_id=self.backtesting_id,
                                                     optimizer_id=self.optimizer_id,
                                                     context=self)
        async with databases.MetaDatabase.database(database_manager, with_lock=with_lock,
                                                   cache_size=cache_size) as meta_db:
            yield meta_db, display
