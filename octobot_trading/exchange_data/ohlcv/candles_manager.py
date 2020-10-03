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
import numpy as np

import octobot_commons.data_util as data_util
import octobot_commons.enums as enums
import octobot_commons.logging as logging

import octobot_trading.util as util


class CandlesManager(util.Initializable):
    MAX_CANDLES_COUNT = 1000

    def __init__(self):
        super().__init__()
        self.logger = logging.get_logger(self.__class__.__name__)

        self.candles_initialized = False

        self.close_candles_index = 0
        self.open_candles_index = 0
        self.high_candles_index = 0
        self.low_candles_index = 0
        self.time_candles_index = 0
        self.volume_candles_index = 0

        self.close_candles = None
        self.open_candles = None
        self.high_candles = None
        self.low_candles = None
        self.time_candles = None
        self.volume_candles = None

        self.reached_max = False
        self._reset_candles()

    async def initialize_impl(self):
        self._reset_candles()

    def _reset_candles(self):
        self.candles_initialized = False
        self.reached_max = False

        self.close_candles_index = 0
        self.open_candles_index = 0
        self.high_candles_index = 0
        self.low_candles_index = 0
        self.time_candles_index = 0
        self.volume_candles_index = 0

        self.close_candles = np.full(CandlesManager.MAX_CANDLES_COUNT, fill_value=np.nan, dtype=np.float64)
        self.open_candles = np.full(CandlesManager.MAX_CANDLES_COUNT, fill_value=np.nan, dtype=np.float64)
        self.high_candles = np.full(CandlesManager.MAX_CANDLES_COUNT, fill_value=np.nan, dtype=np.float64)
        self.low_candles = np.full(CandlesManager.MAX_CANDLES_COUNT, fill_value=np.nan, dtype=np.float64)
        self.time_candles = np.full(CandlesManager.MAX_CANDLES_COUNT, fill_value=np.nan, dtype=np.float64)
        self.volume_candles = np.full(CandlesManager.MAX_CANDLES_COUNT, fill_value=np.nan, dtype=np.float64)

    # getters
    def get_symbol_close_candles(self, limit=-1):
        return self._extract_limited_data(self.close_candles, limit, max_limit=self.close_candles_index)

    def get_symbol_open_candles(self, limit=-1):
        return self._extract_limited_data(self.open_candles, limit, max_limit=self.open_candles_index)

    def get_symbol_high_candles(self, limit=-1):
        return self._extract_limited_data(self.high_candles, limit, max_limit=self.high_candles_index)

    def get_symbol_low_candles(self, limit=-1):
        return self._extract_limited_data(self.low_candles, limit, max_limit=self.low_candles_index)

    def get_symbol_time_candles(self, limit=-1):
        return self._extract_limited_data(self.time_candles, limit, max_limit=self.time_candles_index)

    def get_symbol_volume_candles(self, limit=-1):
        return self._extract_limited_data(self.volume_candles, limit, max_limit=self.volume_candles_index)

    def get_symbol_prices(self, limit=-1):
        return {
            enums.PriceIndexes.IND_PRICE_CLOSE.value: self.get_symbol_close_candles(limit),
            enums.PriceIndexes.IND_PRICE_OPEN.value: self.get_symbol_open_candles(limit),
            enums.PriceIndexes.IND_PRICE_HIGH.value: self.get_symbol_high_candles(limit),
            enums.PriceIndexes.IND_PRICE_LOW.value: self.get_symbol_low_candles(limit),
            enums.PriceIndexes.IND_PRICE_VOL.value: self.get_symbol_volume_candles(limit),
            enums.PriceIndexes.IND_PRICE_TIME.value: self.get_symbol_time_candles(limit)
        }

    def replace_all_candles(self, all_candles_data):
        self._reset_candles()
        self._set_all_candles(all_candles_data)
        self.candles_initialized = True

    def add_old_and_new_candles(self, candles_data):
        """
        Same as add_new_candle but also checks if old candles are missing
        :param candles_data: new candles data
        :return:
        """
        # check old candles
        for old_candle in candles_data[:-1]:
            if old_candle[enums.PriceIndexes.IND_PRICE_TIME.value] not in self.time_candles:
                self.add_new_candle(old_candle)

        try:
            self.add_new_candle(candles_data[-1])
        except IndexError as e:
            self.logger.error(f"Fail to add last candle {candles_data} : {e}")

    def add_new_candle(self, new_candle_data):
        """
        :param new_candle_data: new candles data
        :return:
        """
        if self._should_add_new_candle(new_candle_data[enums.PriceIndexes.IND_PRICE_TIME.value]):
            try:
                self._check_max_candles()
                self.close_candles[self.close_candles_index] = new_candle_data[enums.PriceIndexes.IND_PRICE_CLOSE.value]
                self.open_candles[self.open_candles_index] = new_candle_data[enums.PriceIndexes.IND_PRICE_OPEN.value]
                self.high_candles[self.high_candles_index] = new_candle_data[enums.PriceIndexes.IND_PRICE_HIGH.value]
                self.low_candles[self.low_candles_index] = new_candle_data[enums.PriceIndexes.IND_PRICE_LOW.value]
                self.time_candles[self.time_candles_index] = new_candle_data[enums.PriceIndexes.IND_PRICE_TIME.value]
                self.volume_candles[self.volume_candles_index] = new_candle_data[enums.PriceIndexes.IND_PRICE_VOL.value]
                self._inc_candle_index()
            except IndexError as e:
                self.logger.error(f"Fail to add new candle {new_candle_data} : {e}")

    # private
    def _set_all_candles(self, new_candles_data):
        if isinstance(new_candles_data[-1], list):
            for candle_data in new_candles_data:
                self.add_new_candle(candle_data)
        else:
            self.add_new_candle(new_candles_data)

    def _change_current_candle(self):
        self.close_candles = data_util.shift_value_array(self.close_candles, -1, np.nan, np.float64)
        self.open_candles = data_util.shift_value_array(self.open_candles, -1, np.nan, np.float64)
        self.high_candles = data_util.shift_value_array(self.high_candles, -1, np.nan, np.float64)
        self.low_candles = data_util.shift_value_array(self.low_candles, -1, np.nan, np.float64)
        self.volume_candles = data_util.shift_value_array(self.volume_candles, -1, np.nan, np.float64)
        self.time_candles = data_util.shift_value_array(self.time_candles, -1, np.nan, np.float64)

    def _should_add_new_candle(self, new_open_time):
        return new_open_time not in self.time_candles

    def _check_max_candles(self):
        if self.reached_max:
            self._change_current_candle()

    def _inc_candle_index(self):
        if self.close_candles_index < CandlesManager.MAX_CANDLES_COUNT - 1:
            self.close_candles_index += 1
            self.open_candles_index += 1
            self.high_candles_index += 1
            self.low_candles_index += 1
            self.time_candles_index += 1
            self.volume_candles_index += 1
        else:
            self.reached_max = True

    def _extract_limited_data(self, data, limit=-1, max_limit=-1):
        max_handled_limit: int = self.MAX_CANDLES_COUNT if self.reached_max else max_limit
        if limit == -1:
            if max_limit == -1:
                return np.array(data)
            return np.array(data[:max_handled_limit])

        if max_limit == -1:
            return np.array(data[-min(limit, len(data)):])
        else:
            return np.array(data[max(0, max_handled_limit - limit): max_handled_limit])
