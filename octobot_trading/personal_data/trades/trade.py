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
import decimal
import copy

import octobot_trading.constants as constants
import octobot_trading.enums as enums
import octobot_trading.personal_data.orders.order as order_import
import octobot_commons.symbols as commons_symbols


class Trade:
    CLOSING_TRADE_ORDER_STATUS = {enums.OrderStatus.CANCELED, enums.OrderStatus.FILLED, enums.OrderStatus.CLOSED}

    def __init__(self, trader):
        self.trader = trader
        self.exchange_manager = trader.exchange_manager

        self.status = enums.OrderStatus.OPEN
        self.creation_time = self.exchange_manager.exchange.get_exchange_current_time()

        self.trade_id = trader.parse_order_id(None)
        self.origin_order_id = None
        self.exchange_order_id = None
        # One order might create multiple trades when matched to multiple open orders.
        # in this case those trades would share the same exchange_order_id
        self.exchange_trade_id = None
        self.simulated = True
        self.is_closing_order = False
        self.is_from_this_octobot = True

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
        self.reduce_only = False
        self.tag = None
        self.quantity_currency = None
        self.associated_entry_ids = None

        # raw exchange trade type, used to create trade dict
        self.exchange_trade_type = None

    def update_from_order(self, order, creation_time=0, canceled_time=0, executed_time=0, exchange_trade_id=None):
        self.currency = order.currency
        self.market = order.market
        self.taker_or_maker = order.taker_or_maker
        self.executed_quantity = order.filled_quantity
        self.executed_price = order.filled_price
        self.origin_price = order.origin_price
        self.origin_quantity = order.origin_quantity
        self.total_cost = order.total_cost
        self.quantity_currency = order.quantity_currency
        self.trade_type = order.order_type
        self.exchange_trade_type = order.exchange_order_type
        self.status = order.status
        self.fee = order.fee
        self.trade_id = order.order_id
        self.origin_order_id = order.order_id
        self.exchange_order_id = order.exchange_order_id
        self.exchange_trade_id = exchange_trade_id or self.exchange_trade_id
        self.simulated = order.simulated
        self.side = order.side
        self.creation_time = order.creation_time if order.creation_time > 0 else creation_time
        self.canceled_time = order.canceled_time if order.canceled_time > 0 else canceled_time
        self.executed_time = order.executed_time if order.executed_time > 0 else executed_time
        self.symbol = order.symbol
        self.is_closing_order = order.status in self.CLOSING_TRADE_ORDER_STATUS
        self.is_from_this_octobot = order.is_from_this_octobot
        self.reduce_only = order.reduce_only
        self.tag = order.tag
        self.associated_entry_ids = order.associated_entry_ids

    def get_time(self):
        return self.executed_time if self.has_been_executed() else self.canceled_time

    def get_quantity(self):
        return self.executed_quantity if self.has_been_executed() else self.origin_quantity

    def has_been_executed(self):
        return self.status is not enums.OrderStatus.CANCELED and self.status is not enums.OrderStatus.EXPIRED

    def to_dict(self):
        return {
            enums.ExchangeConstantsOrderColumns.ID.value: self.trade_id,
            enums.ExchangeConstantsOrderColumns.ORDER_ID.value: self.origin_order_id,
            enums.ExchangeConstantsOrderColumns.EXCHANGE_ID.value: self.exchange_order_id,
            enums.ExchangeConstantsOrderColumns.EXCHANGE_TRADE_ID.value: self.exchange_trade_id,
            enums.ExchangeConstantsOrderColumns.SYMBOL.value: self.symbol,
            enums.ExchangeConstantsOrderColumns.MARKET.value: self.market,
            enums.ExchangeConstantsOrderColumns.PRICE.value: self.executed_price,
            enums.ExchangeConstantsOrderColumns.STATUS.value: self.status.value,
            enums.ExchangeConstantsOrderColumns.TIMESTAMP.value: self.get_time(),
            enums.ExchangeConstantsOrderColumns.TYPE.value: self.exchange_trade_type.value,
            enums.ExchangeConstantsOrderColumns.SIDE.value: self.side.value,
            enums.ExchangeConstantsOrderColumns.AMOUNT.value: self.get_quantity(),
            enums.ExchangeConstantsOrderColumns.COST.value: self.total_cost,
            enums.ExchangeConstantsOrderColumns.QUANTITY_CURRENCY.value: self.quantity_currency,
            enums.ExchangeConstantsOrderColumns.TAKER_OR_MAKER.value: self.taker_or_maker,
            enums.ExchangeConstantsOrderColumns.FEE.value: self.fee,
            enums.ExchangeConstantsOrderColumns.REDUCE_ONLY.value: self.reduce_only,
            enums.ExchangeConstantsOrderColumns.TAG.value: self.tag,
            enums.ExchangeConstantsOrderColumns.ENTRIES.value: self.associated_entry_ids,
            enums.TradeExtraConstants.CREATION_TIME.value: self.creation_time,
        }

    @classmethod
    def from_dict(cls, trader, trade_dict):
        trade = cls(trader)
        trade.trade_id = trade_dict.get(enums.ExchangeConstantsOrderColumns.ID.value, trade.trade_id)
        trade.origin_order_id = trade_dict.get(enums.ExchangeConstantsOrderColumns.ORDER_ID.value)
        trade.exchange_trade_id = trade_dict.get(enums.ExchangeConstantsOrderColumns.EXCHANGE_TRADE_ID.value)
        trade.exchange_order_id = trade_dict.get(enums.ExchangeConstantsOrderColumns.EXCHANGE_ID.value)
        trade.symbol = trade_dict.get(enums.ExchangeConstantsOrderColumns.SYMBOL.value)
        trade.currency, trade.market = commons_symbols.parse_symbol(trade.symbol).base_and_quote()
        trade.market = trade_dict.get(enums.ExchangeConstantsOrderColumns.MARKET.value)
        trade.executed_price = decimal.Decimal(str(trade_dict.get(enums.ExchangeConstantsOrderColumns.PRICE.value)))
        trade.status = enums.OrderStatus(trade_dict.get(enums.ExchangeConstantsOrderColumns.STATUS.value,
                                                        enums.OrderStatus.CLOSED.value))
        if trade.has_been_executed():
            trade.executed_time = trade_dict.get(enums.ExchangeConstantsOrderColumns.TIMESTAMP.value)
            trade.executed_quantity = \
                decimal.Decimal(str(trade_dict.get(enums.ExchangeConstantsOrderColumns.AMOUNT.value)))
        else:
            trade.canceled_time = trade_dict.get(enums.ExchangeConstantsOrderColumns.TIMESTAMP.value)
            trade.origin_quantity = \
                decimal.Decimal(str(trade_dict.get(enums.ExchangeConstantsOrderColumns.AMOUNT.value)))
        trade.exchange_trade_type = enums.TradeOrderType(trade_dict.get(enums.ExchangeConstantsOrderColumns.TYPE.value))
        trade.side = enums.TradeOrderSide(trade_dict.get(enums.ExchangeConstantsOrderColumns.SIDE.value))
        trade.trade_type = order_import.parse_order_type({
            enums.ExchangeConstantsOrderColumns.SIDE.value: trade.side.value,
            enums.ExchangeConstantsOrderColumns.TYPE.value: trade.exchange_trade_type.value,
        })[1]
        trade.total_cost = decimal.Decimal(str(trade_dict.get(enums.ExchangeConstantsOrderColumns.COST.value)))
        trade.quantity_currency = trade_dict.get(enums.ExchangeConstantsOrderColumns.QUANTITY_CURRENCY.value)
        trade.taker_or_maker = trade_dict.get(enums.ExchangeConstantsOrderColumns.TAKER_OR_MAKER.value)
        trade.fee = copy.copy(trade_dict.get(enums.ExchangeConstantsOrderColumns.FEE.value))
        if trade.fee and enums.FeePropertyColumns.COST.value in trade.fee:
            trade.fee[enums.FeePropertyColumns.COST.value] = \
                decimal.Decimal(str(trade.fee[enums.FeePropertyColumns.COST.value]))
        trade.reduce_only = trade_dict.get(enums.ExchangeConstantsOrderColumns.REDUCE_ONLY.value)
        trade.tag = trade_dict.get(enums.ExchangeConstantsOrderColumns.TAG.value)
        trade.associated_entry_ids = trade_dict.get(enums.ExchangeConstantsOrderColumns.ENTRIES.value)
        trade.creation_time = trade_dict.get(enums.TradeExtraConstants.CREATION_TIME.value)
        return trade

    def clear(self):
        self.trader = None
        self.exchange_manager = None
