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
from typing import Union, List, Dict

import numpy as np
from scipy.ndimage.interpolation import shift

from octobot_commons.enums import PriceIndexes
from octobot_commons.logging.logging_util import get_logger

from octobot_trading.util.initializable import Initializable


class CandlesManager(Initializable):
    MAX_CANDLES_COUNT = 1000

    def __init__(self):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)

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
        self.__reset_candles()

    async def initialize_impl(self):
        self.__reset_candles()

    def __reset_candles(self):
        self.candles_initialized = False

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
        return self.__extract_limited_data(self.close_candles, limit, max_limit=self.close_candles_index)

    def get_symbol_open_candles(self, limit=-1):
        return self.__extract_limited_data(self.open_candles, limit, max_limit=self.open_candles_index)

    def get_symbol_high_candles(self, limit=-1):
        return self.__extract_limited_data(self.high_candles, limit, max_limit=self.high_candles_index)

    def get_symbol_low_candles(self, limit=-1):
        return self.__extract_limited_data(self.low_candles, limit, max_limit=self.low_candles_index)

    def get_symbol_time_candles(self, limit=-1):
        return self.__extract_limited_data(self.time_candles, limit, max_limit=self.time_candles_index)

    def get_symbol_volume_candles(self, limit=-1):
        return self.__extract_limited_data(self.volume_candles, limit, max_limit=self.volume_candles_index)

    def get_symbol_prices(self, limit=-1):
        return {
            PriceIndexes.IND_PRICE_CLOSE.value: self.get_symbol_close_candles(limit),
            PriceIndexes.IND_PRICE_OPEN.value: self.get_symbol_open_candles(limit),
            PriceIndexes.IND_PRICE_HIGH.value: self.get_symbol_high_candles(limit),
            PriceIndexes.IND_PRICE_LOW.value: self.get_symbol_low_candles(limit),
            PriceIndexes.IND_PRICE_VOL.value: self.get_symbol_volume_candles(limit),
            PriceIndexes.IND_PRICE_TIME.value: self.get_symbol_time_candles(limit)
        }

    def replace_all_candles(self, all_candles_data):
        self.__reset_candles()
        self.__set_all_candles(all_candles_data)
        self.candles_initialized = True

    """
    Same as add_new_candle but also checks if old candles are missing
    """

    def add_old_and_new_candles(self, candles_data):
        # check old candles
        for old_candle in candles_data[:-1]:
            if old_candle[PriceIndexes.IND_PRICE_TIME.value] not in self.time_candles:
                self.add_new_candle(old_candle)

        try:
            self.add_new_candle(candles_data[-1])
        except IndexError as e:
            self.logger.error(f"Fail to add last candle {candles_data} : {e}")

    def add_new_candle(self, new_candle_data: Dict):
        if self.__should_add_new_candle(new_candle_data[PriceIndexes.IND_PRICE_TIME.value]):
            try:
                self.close_candles[self.close_candles_index] = new_candle_data[PriceIndexes.IND_PRICE_CLOSE.value]
                self.open_candles[self.open_candles_index] = new_candle_data[PriceIndexes.IND_PRICE_OPEN.value]
                self.high_candles[self.high_candles_index] = new_candle_data[PriceIndexes.IND_PRICE_HIGH.value]
                self.low_candles[self.low_candles_index] = new_candle_data[PriceIndexes.IND_PRICE_LOW.value]
                self.time_candles[self.time_candles_index] = new_candle_data[PriceIndexes.IND_PRICE_TIME.value]
                self.volume_candles[self.volume_candles_index] = new_candle_data[PriceIndexes.IND_PRICE_VOL.value]
                self.__inc_candle_index()
            except IndexError as e:
                self.logger.error(f"Fail to add new candle {new_candle_data} : {e}")

    # private
    def __set_all_candles(self, new_candles_data: Union[List, Dict]):
        if isinstance(new_candles_data[-1], list):
            for candle_data in new_candles_data:
                self.add_new_candle(candle_data)
        else:
            self.add_new_candle(new_candles_data)

    def __change_current_candle(self):
        shift(self.close_candles, -1, cval=np.NaN)
        shift(self.open_candles, -1, cval=np.NaN)
        shift(self.high_candles, -1, cval=np.NaN)
        shift(self.low_candles, -1, cval=np.NaN)
        shift(self.time_candles, -1, cval=np.NaN)
        shift(self.volume_candles, -1, cval=np.NaN)

    def __should_add_new_candle(self, new_open_time):
        return new_open_time not in self.time_candles

    def __inc_candle_index(self):
        if self.close_candles_index == -1:
            return self.__change_current_candle()

        if self.close_candles_index < CandlesManager.MAX_CANDLES_COUNT:
            self.close_candles_index += 1
            self.open_candles_index += 1
            self.high_candles_index += 1
            self.low_candles_index += 1
            self.time_candles_index += 1
            self.volume_candles_index += 1
        else:
            self.close_candles_index = -1
            self.open_candles_index = -1
            self.high_candles_index = -1
            self.low_candles_index = -1
            self.time_candles_index = -1
            self.volume_candles_index = -1

    def __extract_limited_data(self, data, limit=-1, max_limit=-1):
        if limit == -1:
            if max_limit == -1:
                return data
            return data[:max_limit]

        if max_limit == -1:
            return data[-min(limit, len(data)):]
        else:
            return data[max_limit - limit:max_limit]
