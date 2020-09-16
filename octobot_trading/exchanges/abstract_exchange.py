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
import time
from octobot_commons.enums import PriceIndexes
from octobot_commons.logging.logging_util import get_logger
from octobot_commons.timestamp_util import is_valid_timestamp

from octobot_trading.constants import DEFAULT_EXCHANGE_TIME_LAG
from octobot_trading.util.initializable import Initializable


class AbstractExchange(Initializable):
    def __init__(self, config, exchange_type, exchange_manager):
        super().__init__()
        self.config = config
        self.exchange_type = exchange_type
        self.exchange_manager = exchange_manager
        self.name = self.exchange_type.__name__
        self.logger = get_logger(f"{self.__class__.__name__}[{self.name}]")
        self.allowed_time_lag = DEFAULT_EXCHANGE_TIME_LAG

    async def initialize_impl(self):
        raise NotImplementedError("initialize_impl not implemented")

    def get_uniform_timestamp(self, timestamp):
        raise NotImplementedError("get_uniform_timestamp not implemented")

    @classmethod
    def get_name(cls) -> str:
        raise NotImplementedError("get_name is not implemented")

    def get_exchange_current_time(self):
        """
        Default implementation, should return exchange current time
        :return: the exchange current time
        """
        return time.time()

    def need_to_uniformize_timestamp(self, timestamp):
        """
        Return True if the timestamp should be uniformized
        :param timestamp: the timestamp to check
        :return: True if the timestamp should be uniformized
        """
        return not is_valid_timestamp(timestamp)

    def get_uniformized_timestamp(self, timestamp):
        """
        Uniformize a timestamp
        :param timestamp: the timestamp to uniform
        :return: the timestamp uniformized
        """
        if self.need_to_uniformize_timestamp(timestamp):
            return self.get_uniform_timestamp(timestamp)
        return timestamp

    def uniformize_candles_if_necessary(self, candle_or_candles):
        """
        Uniform timestamps of a list of candles or a candle
        :param candle_or_candles: a list of candles or a candle to be uniformized
        :return: the list of candles or the candle uniformized
        """
        if candle_or_candles:  # TODO improve
            if isinstance(candle_or_candles[0], list):
                if self.need_to_uniformize_timestamp(candle_or_candles[0][PriceIndexes.IND_PRICE_TIME.value]):
                    self._uniformize_candles_timestamps(candle_or_candles)
            else:
                if self.need_to_uniformize_timestamp(candle_or_candles[PriceIndexes.IND_PRICE_TIME.value]):
                    self._uniformize_candle_timestamps(candle_or_candles)
        return candle_or_candles

    def _uniformize_candles_timestamps(self, candles):
        """
        Uniformize a list candle timestamps
        :param candles: the list of candles to uniformize
        """
        for candle in candles:
            self._uniformize_candle_timestamps(candle)

    def _uniformize_candle_timestamps(self, candle):
        """
        Uniformize a candle timestamp
        :param candle: the candle to uniformize
        """
        candle[PriceIndexes.IND_PRICE_TIME.value] = \
            self.get_uniform_timestamp(candle[PriceIndexes.IND_PRICE_TIME.value])
