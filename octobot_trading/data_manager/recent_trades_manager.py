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
from collections import deque

from octobot_commons.logging.logging_util import get_logger

from octobot_trading.util.initializable import Initializable


class RecentTradesManager(Initializable):
    MAX_RECENT_TRADES_COUNT = 100
    MAX_LIQUIDATIONS_COUNT = 20

    def __init__(self, price_events_manager):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.price_events_manager = price_events_manager
        self.recent_trades = deque(maxlen=self.MAX_RECENT_TRADES_COUNT)
        self.liquidations = deque(maxlen=self.MAX_LIQUIDATIONS_COUNT)
        self._reset_recent_trades()

    async def initialize_impl(self):
        self.price_events_manager.reset()
        self._reset_recent_trades()

    def set_all_recent_trades(self, recent_trades):
        if recent_trades:
            self.recent_trades = recent_trades
            self.price_events_manager.handle_recent_trades(self.recent_trades)
            return self.recent_trades

    def add_new_trades(self, recent_trades):
        if recent_trades:
            new_recent_trades: list = [
                trade
                for trade in recent_trades
                if trade not in self.recent_trades]
            self.recent_trades.extend(new_recent_trades)
            self.price_events_manager.handle_recent_trades(new_recent_trades)
            return new_recent_trades

    def add_new_liquidations(self, liquidations):
        if liquidations:
            new_liquidations: list = [
                liquidation
                for liquidation in liquidations
                if liquidation not in self.liquidations]
            self.liquidations.extend(new_liquidations)
            return new_liquidations

    def _reset_recent_trades(self):
        self.recent_trades = deque(maxlen=self.MAX_RECENT_TRADES_COUNT)
        self.liquidations = deque(maxlen=self.MAX_LIQUIDATIONS_COUNT)
