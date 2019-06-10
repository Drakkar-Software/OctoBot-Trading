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
from octobot_commons.logging.logging_util import get_logger

from octobot_trading.util.initializable import Initializable


class RecentTradesManager(Initializable):
    MAX_TRADES_COUNT = 100

    def __init__(self):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.recent_trades = []
        self._reset_recent_trades()

    async def initialize_impl(self):
        self._reset_recent_trades()

    def _reset_recent_trades(self):
        self.recent_trades = []

    def recent_trades_update(self, recent_trades):
        if recent_trades:
            self.recent_trades = recent_trades

    def recent_trade_update(self, recent_trade):
        if recent_trade:
            if self.MAX_TRADES_COUNT > len(self.recent_trades) > 0:
                self.recent_trades.pop(0)
            self.recent_trades += recent_trade
