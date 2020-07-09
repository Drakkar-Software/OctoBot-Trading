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
from octobot_trading.enums import OrderStatus, ExchangeConstantsOrderColumns


class Trade:
    def __init__(self, trader):
        self.trader = trader
        self.exchange_manager = trader.exchange_manager

        self.status = OrderStatus.OPEN
        self.creation_time = self.exchange_manager.exchange.get_exchange_current_time()

        self.trade_id = trader.parse_order_id(None)
        self.simulated = True

        self.symbol = None
        self.currency = None
        self.market = None
        self.taker_or_maker = None
        self.origin_price = 0
        self.origin_quantity = 0
        self.trade_type = None
        self.side = None
        self.executed_quantity = 0
        self.canceled_time = 0
        self.executed_time = 0
        self.fee = None
        self.executed_price = 0
        self.trade_profitability = 0
        self.total_cost = 0

        # raw exchange trade type, used to create trade dict
        self.exchange_trade_type = None

    def update_from_order(self, order, creation_time=0, canceled_time=0, executed_time=0):
        self.currency, self.market = order.get_currency_and_market()
        self.taker_or_maker = order.taker_or_maker
        self.executed_quantity = order.filled_quantity
        self.executed_price = order.filled_price
        self.origin_price = order.origin_price
        self.origin_quantity = order.origin_quantity
        self.total_cost = order.total_cost
        self.trade_type = order.order_type
        self.exchange_trade_type = order.exchange_order_type
        self.status = order.status
        self.fee = order.fee
        self.trade_id = order.order_id
        self.simulated = order.simulated
        self.side = order.side
        self.creation_time = order.creation_time if order.creation_time > 0 else creation_time
        self.canceled_time = order.canceled_time if order.canceled_time > 0 else canceled_time
        self.executed_time = order.executed_time if order.executed_time > 0 else executed_time
        self.symbol = order.symbol

    def to_dict(self):
        trade_time = self.executed_time if self.status is not OrderStatus.CANCELED else self.canceled_time
        return {
            ExchangeConstantsOrderColumns.ID.value: self.trade_id,
            ExchangeConstantsOrderColumns.SYMBOL.value: self.symbol,
            ExchangeConstantsOrderColumns.PRICE.value: self.executed_price,
            ExchangeConstantsOrderColumns.STATUS.value: self.status.value,
            ExchangeConstantsOrderColumns.TIMESTAMP.value: trade_time,
            ExchangeConstantsOrderColumns.TYPE.value: self.exchange_trade_type.value,
            ExchangeConstantsOrderColumns.SIDE.value: self.side.value,
            ExchangeConstantsOrderColumns.AMOUNT.value: self.executed_quantity,
            ExchangeConstantsOrderColumns.COST.value: self.total_cost,
            ExchangeConstantsOrderColumns.TAKERORMAKER.value: self.taker_or_maker,
            ExchangeConstantsOrderColumns.FEE.value: self.fee
        }
