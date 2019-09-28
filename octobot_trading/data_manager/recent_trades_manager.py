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
        self.recent_trades_initialized = False
        self.__reset_recent_trades()

    async def initialize_impl(self):
        self.__reset_recent_trades()

    def set_all_recent_trades(self, recent_trades):
        if recent_trades:
            self.recent_trades = list(set(recent_trades))
            self.__check_recent_trades_size()
            self.recent_trades_initialized = True
            return self.recent_trades

    def add_new_trades(self, recent_trades):
        if recent_trades:
            new_recent_trades: list = [
                trade
                for trade in recent_trades
                if trade not in self.recent_trades]
            self.recent_trades += new_recent_trades
            self.__check_recent_trades_size()
            return new_recent_trades

    def add_recent_trade(self, recent_trade):
        try:
            if recent_trade not in self.recent_trades:
                self.recent_trades.append(recent_trade)
                self.__check_recent_trades_size()
                return recent_trade
        except ValueError as e:
            self.logger.error(f"Impossible to add new recent trade ({recent_trade} : {e})")

    def __reset_recent_trades(self):
        self.recent_trades_initialized = False
        self.recent_trades = []

    def __check_recent_trades_size(self):
        if self.MAX_TRADES_COUNT == len(self.recent_trades):
            self.recent_trades.pop(0)
        elif self.MAX_TRADES_COUNT < len(self.recent_trades):
            self.recent_trades = self.recent_trades[-self.MAX_TRADES_COUNT:]
