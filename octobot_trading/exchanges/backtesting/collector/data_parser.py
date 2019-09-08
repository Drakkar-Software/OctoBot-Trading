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

from octobot_commons.enums import PriceIndexes

from octobot_trading.constants import BACKTESTING_DATA_OHLCV, BACKTESTING_DATA_TRADES
from octobot_trading.enums import BacktestingDataFormats
from octobot_trading.exchanges.backtesting.collector import BacktestingDataFileException
from octobot_trading.exchanges.backtesting.collector.data_file_manager import read_data_file, get_data_type


class DataCollectorParser:
    @staticmethod
    def parse(file_path: str, file: str) -> dict:
        if os.path.isfile(os.path.join(file_path, file)):
            file_content = DataCollectorParser._get_file_content(os.path.join(file_path, file))
        else:
            file_content = DataCollectorParser._get_file_content(file)
        return file_content

    @staticmethod
    def _get_file_content(file_name):
        file_content = read_data_file(file_name)
        data_type = get_data_type(file_name)
        if data_type == BacktestingDataFormats.REGULAR_COLLECTOR_DATA:
            return DataCollectorParser._merge_arrays(file_content)
        else:
            raise BacktestingDataFileException(file_name)

    @staticmethod
    def _merge_arrays(arrays):
        parsed_data = DataCollectorParser._get_empty_parsed_data()
        ohlcv_data = parsed_data[BACKTESTING_DATA_OHLCV]
        for time_frame in arrays:
            data = arrays[time_frame]
            ohlcv_data[time_frame] = []
            for i in range(len(data[PriceIndexes.IND_PRICE_TIME.value])):
                ohlcv_data[time_frame].insert(i, [None]*len(PriceIndexes))
                ohlcv_data[time_frame][i][PriceIndexes.IND_PRICE_CLOSE.value] = \
                    data[PriceIndexes.IND_PRICE_CLOSE.value][i]
                ohlcv_data[time_frame][i][PriceIndexes.IND_PRICE_OPEN.value] = \
                    data[PriceIndexes.IND_PRICE_OPEN.value][i]
                ohlcv_data[time_frame][i][PriceIndexes.IND_PRICE_HIGH.value] = \
                    data[PriceIndexes.IND_PRICE_HIGH.value][i]
                ohlcv_data[time_frame][i][PriceIndexes.IND_PRICE_LOW.value] = \
                    data[PriceIndexes.IND_PRICE_LOW.value][i]
                ohlcv_data[time_frame][i][PriceIndexes.IND_PRICE_TIME.value] = \
                    data[PriceIndexes.IND_PRICE_TIME.value][i]
                ohlcv_data[time_frame][i][PriceIndexes.IND_PRICE_VOL.value] = \
                    data[PriceIndexes.IND_PRICE_VOL.value][i]

        return parsed_data

    @staticmethod
    def _get_empty_parsed_data():
        return {
            BACKTESTING_DATA_OHLCV: {},
            BACKTESTING_DATA_TRADES: {}
        }
