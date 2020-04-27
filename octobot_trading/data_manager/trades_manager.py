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

from octobot_trading.enums import FeePropertyColumns
from octobot_trading.trades.trade_factory import create_trade_instance_from_raw
from octobot_trading.util.initializable import Initializable


class TradesManager(Initializable):
    MAX_TRADES_COUNT = 500

    def __init__(self, config, trader, exchange_manager):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.config, self.trader, self.exchange_manager = config, trader, exchange_manager
        self.trades_initialized = False
        self.trades = OrderedDict()

    async def initialize_impl(self):
        self._reset_trades()
        self.trades_initialized = True

    def upsert_trade(self, trade_id, raw_trade):
        if trade_id not in self.trades:
            created_trade = create_trade_instance_from_raw(self.trader, raw_trade)
            if created_trade:
                self.trades[trade_id] = created_trade
                self._check_trades_size()
                return True
        return False

    def upsert_trade_instance(self, trade):
        if trade.trade_id not in self.trades:
            self.trades[trade.trade_id] = trade
            self._check_trades_size()

    def get_total_paid_fees(self):
        total_fees = {}
        for trade in self.trades.values():
            if trade.fee is not None:
                fee_cost = trade.fee[FeePropertyColumns.COST.value]
                fee_currency = trade.fee[FeePropertyColumns.CURRENCY.value]
                if fee_currency in total_fees:
                    total_fees[fee_currency] += fee_cost
                else:
                    total_fees[fee_currency] = fee_cost
            else:
                self.logger.warning(f"Trade without any registered fee: {trade}")
        return total_fees

    def get_trade(self, trade_id):
        return self.trades[trade_id]

    # private
    def _check_trades_size(self):
        if len(self.trades) > self.MAX_TRADES_COUNT:
            self._remove_oldest_trades(int(self.MAX_TRADES_COUNT / 2))

    def _reset_trades(self):
        self.trades_initialized = False
        self.trades = OrderedDict()

    def _remove_oldest_trades(self, nb_to_remove):
        for _ in range(nb_to_remove):
            self.trades.popitem(last=False)

    def clear(self):
        for trade in self.trades.values():
            trade.trader = None
            trade.exchange_manager = None
        self._reset_trades()
