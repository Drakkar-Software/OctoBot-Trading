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
from math import nan
from octobot_commons.enums import PriceIndexes
from octobot_commons.logging.logging_util import get_logger

from octobot_trading.util.initializable import Initializable


class KlineManager(Initializable):
    def __init__(self):  # Required for python development
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.kline = []

    async def initialize_impl(self):
        self._reset_kline()

    def _reset_kline(self):
        self.kline = [nan] * len(PriceIndexes)

    def _update_kline_key(self, kline_key, kline_update):
        try:
            if kline_update[kline_key] is not nan:
                self.kline[kline_key] = kline_update[kline_key]
        except KeyError:
            pass

    def _update_kline_init_only_key(self, kline_key, kline_update):
        try:
            if self.kline[kline_key] is nan:
                self.kline[kline_key] = kline_update[kline_key]
        except KeyError:
            pass

    def kline_update(self, kline):
        try:
            # test for new candle
            if self.kline[PriceIndexes.IND_PRICE_TIME.value] != kline[PriceIndexes.IND_PRICE_TIME.value]:
                self._reset_kline()

            self._update_kline_init_only_key(PriceIndexes.IND_PRICE_TIME.value, kline)
            self._update_kline_init_only_key(PriceIndexes.IND_PRICE_OPEN.value, kline)

            self._update_kline_key(PriceIndexes.IND_PRICE_VOL.value, kline)
            self._update_kline_key(PriceIndexes.IND_PRICE_CLOSE.value, kline)

            if self.kline[PriceIndexes.IND_PRICE_HIGH.value] is nan or \
                    self.kline[PriceIndexes.IND_PRICE_HIGH.value] < kline[PriceIndexes.IND_PRICE_HIGH.value]:
                self._update_kline_key(PriceIndexes.IND_PRICE_HIGH.value, kline)

            if self.kline[PriceIndexes.IND_PRICE_LOW.value] is nan or \
                    self.kline[PriceIndexes.IND_PRICE_LOW.value] > kline[PriceIndexes.IND_PRICE_LOW.value]:
                self._update_kline_key(PriceIndexes.IND_PRICE_LOW.value, kline)
        except TypeError as e:
            self.logger.error(f"Fail to update kline with {kline} : {e}")
