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
        self.recent_trades = set()
        self._reset_recent_trades()

    async def initialize_impl(self):
        self._reset_recent_trades()

    def set_all_recent_trades(self, recent_trades):
        if recent_trades:
            self.recent_trades = set(recent_trades)
            self._check_recent_trades_size()

    def add_new_trades(self, recent_trades):
        if recent_trades:
            self.recent_trades.update(recent_trades)
            self._check_recent_trades_size()

    def add_recent_trade(self, recent_trade):
        try:
            self.recent_trades += recent_trade
            self._check_recent_trades_size()
        except ValueError as e:
            self.logger.error(f"Impossible to add new recent trade ({recent_trade} : {e})")

    def _reset_recent_trades(self):
        self.recent_trades = set()

    def _check_recent_trades_size(self):
        if self.MAX_TRADES_COUNT > len(self.recent_trades) > 0:
            self.recent_trades = self.recent_trades[-self.MAX_TRADES_COUNT:]
