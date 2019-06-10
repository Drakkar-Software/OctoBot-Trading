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

from octobot_trading.enums import ExchangeConstantsTickersColumns
from octobot_trading.util.initializable import Initializable


class TickerManager(Initializable):
    def __init__(self):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.ticker = {}
        self.reset_ticker()

    async def initialize_impl(self):
        self.reset_ticker()

    def reset_ticker(self):
        self.ticker = {
            ExchangeConstantsTickersColumns.ASK: nan,
            ExchangeConstantsTickersColumns.ASK_VOLUME: nan,
            ExchangeConstantsTickersColumns.BID: nan,
            ExchangeConstantsTickersColumns.BID_VOLUME: nan,
            ExchangeConstantsTickersColumns.OPEN: nan,
            ExchangeConstantsTickersColumns.LOW: nan,
            ExchangeConstantsTickersColumns.HIGH: nan,
            ExchangeConstantsTickersColumns.CLOSE: nan,
            ExchangeConstantsTickersColumns.LAST: nan,
            ExchangeConstantsTickersColumns.AVERAGE: nan,
            ExchangeConstantsTickersColumns.SYMBOL: nan,
            ExchangeConstantsTickersColumns.QUOTE_VOLUME: nan,
            ExchangeConstantsTickersColumns.TIMESTAMP: 0,
            ExchangeConstantsTickersColumns.VWAP: nan
        }

    def ticker_update(self, ticker):
        if ticker:
            self.ticker = ticker
