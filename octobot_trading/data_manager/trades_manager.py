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

from octobot_trading.data.order import Order
from octobot_trading.data.trade import Trade
from octobot_trading.enums import ExchangeConstantsOrderColumns
from octobot_trading.util.initializable import Initializable


class TradesManager(Initializable):
    MAX_TRADES_COUNT = 500

    def __init__(self, config, trader, exchange_manager):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.config, self.trader, self.exchange_manager = config, trader, exchange_manager
        self.trades_initialized = False  # TODO
        self.trades = OrderedDict()

    async def initialize_impl(self):
        self._reset_trades()

    def upsert_trade(self, trade_id, raw_trade):
        if trade_id not in self.trades:
            self.trades[trade_id] = self._create_trade_from_raw(raw_trade)
            self._check_trades_size()
            return True
        return False

    # private
    def _check_trades_size(self):
        if len(self.trades) > self.MAX_TRADES_COUNT:
            self._remove_oldest_trades(int(self.MAX_TRADES_COUNT / 2))

    def _create_trade_from_raw(self, raw_trade):
        order = Order(self.trader)
        order.order_id = raw_trade[ExchangeConstantsOrderColumns.ID.value]
        order.origin_price = raw_trade[ExchangeConstantsOrderColumns.PRICE.value]
        order.origin_quantity = raw_trade[ExchangeConstantsOrderColumns.AMOUNT.value]
        order.symbol = raw_trade[ExchangeConstantsOrderColumns.SYMBOL.value]
        order.currency, order.market = self.exchange_manager.get_exchange_quote_and_base(
            raw_trade[ExchangeConstantsOrderColumns.SYMBOL.value])
        order.filled_quantity = raw_trade[ExchangeConstantsOrderColumns.AMOUNT.value]
        order.filled_quantity = None  # TODO
        order.filled_price = None  # TODO
        order.total_cost = None  # TODO
        order.order_type = None  # TODO
        order.fee = None  # TODO
        order.side = None  # TODO
        order.canceled_time = None  # TODO
        order.executed_time = None  # TODO
        return Trade(order)

    def _reset_trades(self):
        self.trades_initialized = False
        self.trades = OrderedDict()

    def _remove_oldest_trades(self, nb_to_remove):
        for _ in range(nb_to_remove):
            self.trades.popitem(last=False)
