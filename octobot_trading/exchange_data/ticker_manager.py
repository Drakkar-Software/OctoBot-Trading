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
from octobot_commons.logging.logging_util import get_logger

from octobot_trading.enums import ExchangeConstantsTickersColumns, ExchangeConstantsMiniTickerColumns
from octobot_trading.util.initializable import Initializable


class TickerManager(Initializable):
    def __init__(self):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.ticker = {}
        self.mini_ticker = {}
        self.reset_ticker()
        self.reset_mini_ticker()

    async def initialize_impl(self):
        self.reset_ticker()
        self.reset_mini_ticker()

    def reset_mini_ticker(self):
        self.mini_ticker = {
            ExchangeConstantsMiniTickerColumns.HIGH_PRICE.value: nan,
            ExchangeConstantsMiniTickerColumns.LOW_PRICE.value: nan,
            ExchangeConstantsMiniTickerColumns.OPEN_PRICE.value: nan,
            ExchangeConstantsMiniTickerColumns.CLOSE_PRICE.value: nan,
            ExchangeConstantsMiniTickerColumns.VOLUME.value: nan,
            ExchangeConstantsMiniTickerColumns.TIMESTAMP.value: 0
        }

    def reset_ticker(self):
        self.ticker = {
            ExchangeConstantsTickersColumns.ASK.value: nan,
            ExchangeConstantsTickersColumns.ASK_VOLUME.value: nan,
            ExchangeConstantsTickersColumns.BID.value: nan,
            ExchangeConstantsTickersColumns.BID_VOLUME.value: nan,
            ExchangeConstantsTickersColumns.OPEN.value: nan,
            ExchangeConstantsTickersColumns.LOW.value: nan,
            ExchangeConstantsTickersColumns.HIGH.value: nan,
            ExchangeConstantsTickersColumns.CLOSE.value: nan,
            ExchangeConstantsTickersColumns.LAST.value: nan,
            ExchangeConstantsTickersColumns.AVERAGE.value: nan,
            ExchangeConstantsTickersColumns.SYMBOL.value: nan,
            ExchangeConstantsTickersColumns.QUOTE_VOLUME.value: nan,
            ExchangeConstantsTickersColumns.TIMESTAMP.value: 0,
            ExchangeConstantsTickersColumns.VWAP.value: nan
        }

    def ticker_update(self, ticker):
        self.ticker.update(ticker)

    def mini_ticker_update(self, mini_ticker):
        self.mini_ticker.update(mini_ticker)
