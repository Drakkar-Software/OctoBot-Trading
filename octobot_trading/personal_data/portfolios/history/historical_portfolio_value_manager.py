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
import sortedcontainers

import octobot_commons.logging as logging
import octobot_commons.databases as databases
import octobot_commons.constants as commons_constants
import octobot_commons.enums as commons_enums
import octobot_commons.symbol_util as symbol_util

import octobot_trading.util as util
import octobot_trading.errors as errors
import octobot_trading.constants as constants
import octobot_trading.storage as storage
import octobot_trading.personal_data.portfolios.history.historical_asset_value as historical_asset_value
import octobot_trading.personal_data.portfolios.history.historical_asset_value_factory as historical_asset_value_factory


class HistoricalPortfolioValueManager(util.Initializable):
    """
    HistoricalPortfolioValueManager stores and make the portfolio value through time as HistoricalAssetValue
    """
    TABLE_NAME = "historical_portfolio_value"
    DATA_SOURCE_KEY = "data_source"
    DATA_VERSION_KEY = "data_version"
    DEFAULT_DATA_SOURCE = "portfolio_value_holder"  # for later versions: consolidate data with transaction history
    DEFAULT_DATA_VERSION = "1.0.0"
    MIN_TIME_FRAME_RELEVANCY_SECONDS = 29   # less than 30s to support 1m time frames
    TIME_FRAME_RELEVANCY_TIME_RATIO = 0.45   # allow for 45% error in timestamp rounding (only used after the ideal
    # time passed to avoid using past data: use future data at worse). use high value to still take value if users
    # start it in the 1st part of the day for example
    MAX_HISTORY_SIZE = 250000

    def __init__(self, portfolio_manager, data_source=None, version=None):
        super().__init__()
        self.portfolio_manager = portfolio_manager
        self.logger = logging.get_logger(f"{self.__class__.__name__}"
                                         f"[{self.portfolio_manager.exchange_manager.exchange_name}]")
        self._portfolio_type_suffix = self._get_portfolio_type_suffix()
        self.saved_time_frames = self.portfolio_manager.exchange_manager.config.get(
            commons_constants.CONFIG_SAVED_HISTORICAL_TIMEFRAMES,
            constants.DEFAULT_SAVED_HISTORICAL_TIMEFRAMES
        )
        self.data_source = data_source or self.__class__.DEFAULT_DATA_SOURCE
        self.version = version or self.__class__.DEFAULT_DATA_VERSION

        self.max_history_size = self.__class__.MAX_HISTORY_SIZE
        self.historical_portfolio_value = sortedcontainers.SortedDict()
        try:
            self.run_dbs_identifier = storage.RunDatabasesProvider.instance().get_run_databases_identifier(
                self.portfolio_manager.exchange_manager.bot_id
            )
        except KeyError:
            # can't save data without an activated trading mode
            self.run_dbs_identifier = None

    async def initialize_impl(self):
        """
        Reset the portfolio instance
        """
        await self._reload_historical_portfolio_value()

    async def on_new_value(self, timestamp, value_by_currency, force_update=False, save_changes=True,
                           include_past_data=False):
        """
        Updates the historical value only if the current timestamp or currency is missing, unless force_update is True
        :param timestamp: timestamp associated to the current portfolio value. Will be adapted for each timeframe
        :param value_by_currency: dict of currency and values
        :param force_update: when True, even if timestamp is already associated to a value, the value is still updated
        :param save_changes: when True, updates the database via save_historical_portfolio_value()
        :param include_past_data: when True, also save data from past time periods using their closest relevant
        timestamp
        :return: True if something changed
        """
        # TODO replace by := when cython will support it
        relevant_timestamps = self._get_relevant_timestamps(timestamp, value_by_currency.keys(),
                                                            self.saved_time_frames, force_update, include_past_data)
        if relevant_timestamps:
            return await self._upsert_value(relevant_timestamps, value_by_currency, save_changes)
        return False

    async def on_new_values(self, value_by_currency_by_timestamp, force_update=False, save_changes=True):
        changed = False
        for timestamp, value_by_currency in value_by_currency_by_timestamp.items():
            changed |= await self.on_new_value(timestamp, value_by_currency,
                                               force_update=force_update, save_changes=False,
                                               include_past_data=True)
        if changed and save_changes:
            await self.save_historical_portfolio_value()
        return changed

    def get_historical_values(self, currency, time_frame, from_timestamp=0, to_timestamp=None):
        """
        Returns a dict with timestamps and their associated portfolio historical value. Does not include the current
        portfolio value
        :param currency: the currency to compute value in
        :param time_frame: intervals between values
        :param from_timestamp: selected time window start time
        :param to_timestamp: selected time window end time
        """
        to_timestamp = to_timestamp or self.portfolio_manager.exchange_manager.exchange.get_exchange_current_time()
        time_frame_seconds = commons_enums.TimeFramesMinutes[time_frame] * commons_constants.MINUTE_TO_SECONDS
        relevant_historical_values = [
            value
            for timestamp, value in self.historical_portfolio_value.items()
            if self._is_historical_timestamp_relevant(timestamp, time_frame_seconds, from_timestamp, to_timestamp)
        ]
        historical_values = {}
        for historical_value in relevant_historical_values:
            try:
                historical_values[historical_value.get_timestamp()] = \
                    self._get_value_in_currency(historical_value, currency)
            except errors.MissingPriceDataError as e:
                # do not add missing historical values
                self.logger.debug(f"Missing price data when computing historical portfolio value: {e}")
        return historical_values

    def get_historical_value(self, timestamp):
        return self.historical_portfolio_value[timestamp]

    async def reset_history(self):
        self.historical_portfolio_value = sortedcontainers.SortedDict()
        await self.save_historical_portfolio_value()

    async def _upsert_value(self, timestamps, value_by_currency, save_changes):
        changed = False
        for timestamp in timestamps:
            try:
                changed |= self.get_historical_value(timestamp).update(value_by_currency)
            except KeyError:
                self._add_historical_portfolio_value(timestamp, value_by_currency)
                changed = True
        if changed and save_changes:
            await self.save_historical_portfolio_value()
        return changed

    def _add_historical_portfolio_value(self, timestamp, value_by_currency):
        if len(self.historical_portfolio_value) >= self.max_history_size:
            # remove the oldest element
            self.historical_portfolio_value.popitem(0)
        self.historical_portfolio_value[timestamp] = \
            historical_asset_value.HistoricalAssetValue(timestamp, value_by_currency)

    async def save_historical_portfolio_value(self):
        if self.run_dbs_identifier is None:
            return
        async with databases.DBWriter.database(self.run_dbs_identifier.get_historical_portfolio_value_db_identifier(
                self.portfolio_manager.exchange_manager.exchange_name, self._portfolio_type_suffix
        )) as writer:
            # replace the whole table to ensure consistency
            await writer.upsert(commons_enums.RunDatabases.METADATA.value, self._get_metadata(), None, uuid=1)
            await writer.replace_all(
                self.TABLE_NAME,
                [historical_asset.to_dict() for historical_asset in self.historical_portfolio_value.values()],
                cache=False
            )

    async def _reload_historical_portfolio_value(self):
        if self.run_dbs_identifier is None:
            return
        await self.run_dbs_identifier.initialize(
            exchange=self.portfolio_manager.exchange_manager.exchange_name, from_global_history=True
        )
        async with databases.DBReader.database(self.run_dbs_identifier.get_historical_portfolio_value_db_identifier(
                self.portfolio_manager.exchange_manager.exchange_name, self._portfolio_type_suffix
        )) as reader:
            self._load_historical_values(await reader.all(self.TABLE_NAME))

    def _load_historical_values(self, dict_values):
        self.historical_portfolio_value = sortedcontainers.SortedDict({
            element[historical_asset_value.HistoricalAssetValue.TIMESTAMP_KEY]:
                historical_asset_value_factory.create_historical_asset_value_from_dict(
                    historical_asset_value.HistoricalAssetValue, element
                )
            for element in dict_values
        })

    def _is_historical_timestamp_relevant(self, timestamp, time_frame_seconds, from_timestamp, to_timestamp):
        return self._is_timestamp_relevant(timestamp, time_frame_seconds) and \
               from_timestamp <= timestamp <= to_timestamp

    @staticmethod
    def _is_timestamp_relevant(timestamp, time_frame_seconds):
        return timestamp % time_frame_seconds == 0

    @staticmethod
    def convert_to_historical_timestamp(timestamp, time_frame):
        return timestamp - (timestamp % (
                commons_enums.TimeFramesMinutes[time_frame] * commons_constants.MINUTE_TO_SECONDS
        ))

    def _get_relevant_timestamps(self, timestamp, currencies, time_frames, force_update, include_past_data):
        relevant_timestamps = set()
        current_time = self.portfolio_manager.exchange_manager.exchange.get_exchange_current_time()
        for time_frame in time_frames:
            # allowed times are [local time frame t0: local time frame t0 + allowed lag]
            time_frame_allowed_window_start = self.convert_to_historical_timestamp(
                timestamp if include_past_data else current_time,
                time_frame)
            if self._should_update_timestamp(currencies, time_frame_allowed_window_start, force_update):
                # allow time window if time_frame_allowed_window_start not in self.historical_portfolio_value
                # or when force_update
                time_frame_seconds = commons_enums.TimeFramesMinutes[time_frame] * commons_constants.MINUTE_TO_SECONDS
                time_frame_allowed_window_end = time_frame_allowed_window_start + \
                    max(time_frame_seconds * self.TIME_FRAME_RELEVANCY_TIME_RATIO,
                        self.MIN_TIME_FRAME_RELEVANCY_SECONDS)
                if time_frame_allowed_window_start <= timestamp <= time_frame_allowed_window_end:
                    relevant_timestamps.add(time_frame_allowed_window_start)
        return relevant_timestamps

    def _should_update_timestamp(self, currencies, time_frame_allowed_window_start, force_update):
        if force_update:
            return True
        try:
            for currency in currencies:
                self.get_historical_value(time_frame_allowed_window_start).get(currency)
        except KeyError:
            return True
        return False

    def _get_value_in_currency(self, historical_value, currency):
        try:
            return historical_value.get(currency)
        except KeyError:
            return self._convert_historical_value(historical_value, currency)

    def _convert_historical_value(self, historical_value, target_currency):
        # TODO try to get a more accurate historical value into target_currency currency using price history
        # last chance: try to get any usable value from portfolio value holder (not accurate since used the intermediary
        # asset might also have changed in price since the time it was recorded)
        for currency in historical_value.get_currencies():
            for pair in self.portfolio_manager.portfolio_value_holder.last_prices_by_trading_pair:
                base_and_quote = symbol_util.split_symbol(pair)
                if currency in base_and_quote and target_currency in base_and_quote:
                    return self.portfolio_manager.portfolio_value_holder.convert_currency_value_using_last_prices(
                        historical_value.get(currency), currency, target_currency
                    )
        raise errors.MissingPriceDataError(f"no price data to evaluate {historical_value} on {target_currency}")

    def _get_metadata(self):
        return {
            self.DATA_SOURCE_KEY: self.data_source,
            self.DATA_VERSION_KEY: self.version
        }

    def _get_portfolio_type_suffix(self):
        suffix = ""
        if self.portfolio_manager.exchange_manager.is_future:
            suffix = f"{suffix}_{commons_constants.CONFIG_EXCHANGE_FUTURE}"
        elif self.portfolio_manager.exchange_manager.is_margin:
            suffix = f"{suffix}_{commons_constants.CONFIG_EXCHANGE_MARGIN}"
        else:
            suffix = f"{suffix}_{commons_constants.CONFIG_EXCHANGE_SPOT}"
        if self.portfolio_manager.exchange_manager.is_sandboxed:
            suffix = f"{suffix}_{commons_constants.CONFIG_EXCHANGE_SANDBOXED}"
        if self.portfolio_manager.exchange_manager.is_trader_simulated:
            suffix = f"{suffix}_{commons_constants.CONFIG_SIMULATOR}"
        return suffix

    async def stop(self):
        await self.save_historical_portfolio_value()
