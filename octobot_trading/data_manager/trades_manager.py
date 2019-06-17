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
from collections import OrderedDict

from octobot_commons.logging.logging_util import get_logger

from octobot_trading.data.trade import create_trade_from_dict
from octobot_trading.enums import ExchangeConstantsOrderColumns
from octobot_trading.util.initializable import Initializable


class TradesManager(Initializable):
    MAX_TRADES_COUNT = 500

    def __init__(self, config, trader, exchange_manager):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.config, self.trader, self.exchange_manager = config, trader, exchange_manager
        self.trades = OrderedDict()

    async def initialize_impl(self):
        self._reset_trades()

    def add_new_trades(self, trades):
        if trades:
            new_trades: list = [
                trade
                for trade in trades
                if trade[ExchangeConstantsOrderColumns.ID.value] not in self.trades]

            for trade in new_trades:
                self.trades[trade[ExchangeConstantsOrderColumns.ID.value]] = create_trade_from_dict(self.trader, trade)

            self._check_trades_size()
            return new_trades

    def add_trade(self, trade):
        try:
            if trade[ExchangeConstantsOrderColumns.ID.value] not in self.trades:
                self.trades[trade[ExchangeConstantsOrderColumns.ID.value]] = create_trade_from_dict(self.trader, trade)
                self._check_trades_size()
                return trade
        except ValueError as e:
            self.logger.error(f"Impossible to add new trade ({trade} : {e})")

    def add_trade_instance(self, trade):
        try:
            if trade.order_id not in self.trades:
                self.trades[trade.order_id] = trade
                self._check_trades_size()
                return trade
        except ValueError as e:
            self.logger.error(f"Impossible to add new trade instance ({trade} : {e})")

    def _reset_trades(self):
        self.trades = OrderedDict()

    def _check_trades_size(self):
        while self.MAX_TRADES_COUNT < len(self.trades):
            self.trades.popitem(last=False)
