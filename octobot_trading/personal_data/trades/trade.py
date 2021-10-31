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
import octobot_trading.constants as constants
import octobot_trading.enums as enums


class Trade:
    CLOSING_TRADE_ORDER_STATUS = {enums.OrderStatus.CANCELED, enums.OrderStatus.FILLED, enums.OrderStatus.CLOSED}

    def __init__(self, trader):
        self.trader = trader
        self.exchange_manager = trader.exchange_manager

        self.status = enums.OrderStatus.OPEN
        self.creation_time = self.exchange_manager.exchange.get_exchange_current_time()

        self.trade_id = trader.parse_order_id(None)
        # One order might create multiple trades when matched to multiple open orders.
        # Current implementation creates only one trade per order
        # TODO: update this comment when handling multiple trades per order
        self.origin_order_id = None
        self.simulated = True
        self.is_closing_order = False

        self.symbol = None
        self.currency = None
        self.market = None
        self.taker_or_maker = None
        self.origin_price = constants.ZERO
        self.origin_quantity = constants.ZERO
        self.trade_type = None
        self.side = None
        self.executed_quantity = constants.ZERO
        self.canceled_time = 0
        self.executed_time = 0
        self.fee = None
        self.executed_price = constants.ZERO
        self.trade_profitability = constants.ZERO
        self.total_cost = constants.ZERO

        # raw exchange trade type, used to create trade dict
        self.exchange_trade_type = None

    def update_from_order(self, order, creation_time=0, canceled_time=0, executed_time=0):
        self.currency = order.currency
        self.market = order.market
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
        self.origin_order_id = order.order_id
        self.simulated = order.simulated
        self.side = order.side
        self.creation_time = order.creation_time if order.creation_time > 0 else creation_time
        self.canceled_time = order.canceled_time if order.canceled_time > 0 else canceled_time
        self.executed_time = order.executed_time if order.executed_time > 0 else executed_time
        self.symbol = order.symbol
        self.is_closing_order = order.status in self.CLOSING_TRADE_ORDER_STATUS

    def get_time(self):
        return self.executed_time if self.status is not enums.OrderStatus.CANCELED else self.canceled_time

    def get_quantity(self):
        return self.executed_quantity if self.status is not enums.OrderStatus.CANCELED else self.origin_quantity

    def to_dict(self):
        return {
            enums.ExchangeConstantsOrderColumns.ID.value: self.trade_id,
            enums.ExchangeConstantsOrderColumns.SYMBOL.value: self.symbol,
            enums.ExchangeConstantsOrderColumns.PRICE.value: self.executed_price,
            enums.ExchangeConstantsOrderColumns.STATUS.value: self.status.value,
            enums.ExchangeConstantsOrderColumns.TIMESTAMP.value: self.get_time(),
            enums.ExchangeConstantsOrderColumns.TYPE.value: self.exchange_trade_type.value,
            enums.ExchangeConstantsOrderColumns.SIDE.value: self.side.value,
            enums.ExchangeConstantsOrderColumns.AMOUNT.value: self.get_quantity(),
            enums.ExchangeConstantsOrderColumns.COST.value: self.total_cost,
            enums.ExchangeConstantsOrderColumns.TAKERORMAKER.value: self.taker_or_maker,
            enums.ExchangeConstantsOrderColumns.FEE.value: self.fee
        }
