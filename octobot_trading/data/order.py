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

import time
from asyncio import Lock

import math
from octobot_commons.dict_util import get_value_or_default

from octobot_commons.logging.logging_util import get_logger

from octobot_trading.enums import TradeOrderSide, OrderStatus, TraderOrderType, \
    FeePropertyColumns, ExchangeConstantsMarketPropertyColumns, \
    ExchangeConstantsOrderColumns as ECOC, ExchangeConstantsOrderColumns, TradeOrderType

""" Order class will represent an open order in the specified exchange
In simulation it will also define rules to be filled / canceled
It is also use to store creation & fill values of the order """


class Order:

    def __init__(self, trader):
        self.trader = trader
        self.exchange_manager = trader.exchange_manager
        self.status = OrderStatus.OPEN
        self.creation_time = time.time()
        self.executed_time = 0
        self.lock = Lock()
        self.linked_orders = []

        self.order_id = trader.parse_order_id(None)

        self.symbol = None
        self.currency = None
        self.market = None
        self.taker_or_maker = None
        self.timestamp = 0
        self.origin_price = 0
        self.created_last_price = 0
        self.origin_quantity = 0
        self.origin_stop_price = 0
        self.order_type = None
        self.side = None
        self.filled_quantity = 0
        self.linked_portfolio = None
        self.linked_to = None
        self.canceled_time = 0
        self.fee = None
        self.filled_price = 0
        self.order_profitability = 0
        self.total_cost = 0

    @classmethod
    def get_name(cls):
        return cls.__name__

    def update(self, symbol, order_id="", status=OrderStatus.OPEN,
               current_price=0.0, quantity=0.0, price=0.0, stop_price=0.0,
               quantity_filled=0.0, filled_price=0.0, fee=0.0, total_cost=0.0,
               timestamp=None, linked_to=None, linked_portfolio=None, order_type=None) -> bool:
        changed: bool = False

        if order_id and self.order_id != order_id:
            self.order_id = order_id

        if symbol and self.symbol != symbol:
            self.currency, self.market = self.exchange_manager.get_exchange_quote_and_base(symbol)
            self.symbol = symbol

        if status and self.status != status:
            self.status = status
            changed = True
        if not self.status:
            self.status = OrderStatus.OPEN

        if timestamp and self.timestamp != timestamp:
            self.timestamp = timestamp
        if not self.timestamp:
            if not timestamp:
                self.creation_time = time.time()
            else:
                # if we have a timestamp, it's a real trader => need to format timestamp if necessary
                self.creation_time = self.exchange_manager.exchange.get_uniform_timestamp(timestamp)
            self.timestamp = self.creation_time

        if price and self.origin_price != price:
            self.origin_price = price
            changed = True

        if (fee is not None and self.fee != fee) or quantity_filled is not None:
            self.fee = fee if fee is not None else self.get_computed_fee()

        if current_price and self.created_last_price != current_price:
            self.created_last_price = current_price
            changed = True

        if quantity and self.origin_quantity != quantity:
            self.origin_quantity = quantity
            changed = True

        if stop_price and self.origin_stop_price != stop_price:
            self.origin_stop_price = stop_price
            changed = True

        if total_cost and self.total_cost != total_cost:
            self.total_cost = total_cost

        if filled_price and self.filled_price != filled_price:
            self.filled_price = filled_price

        if self.trader.simulate:
            if quantity and not self.filled_quantity:
                self.filled_quantity = quantity
                changed = True

            if quantity_filled and self.filled_quantity != quantity_filled:
                self.filled_quantity = quantity_filled
                changed = True
        else:
            if quantity_filled and self.filled_quantity != quantity_filled:
                self.filled_quantity = quantity_filled
                changed = True

        if linked_to:
            self.linked_to = linked_to

        if linked_portfolio:
            self.linked_portfolio = linked_portfolio

        if order_type:
            self.order_type = order_type

        if not self.filled_price and self.filled_quantity and self.total_cost:
            self.filled_price = self.total_cost / self.filled_quantity
            if timestamp is not None:
                self.executed_time = self.trader.exchange_manager.exchange.get_uniform_timestamp(timestamp)

        return changed

    async def update_order_status(self, last_prices: list, simulated_time=False):
        """
        Update_order_status will define the rules for a simulated order to be filled / canceled
        """
        raise NotImplementedError("Update_order_status not implemented")

    # check_last_prices is used to collect data to perform the order update_order_status process
    def check_last_prices(self, last_prices, price_to_check, inferior, simulated_time=False) -> bool:
        if last_prices:
            prices = [p[ECOC.PRICE.value]
                      for p in last_prices
                      if not math.isnan(p[ECOC.PRICE.value]) and (
                              p[ECOC.TIMESTAMP.value] >= self.creation_time or simulated_time)]

            if prices:
                if inferior:
                    if float(min(prices)) < price_to_check:
                        get_logger(self.get_name()).debug(f"{self.symbol} last prices: {prices}, "
                                                          f"ask for {'inferior' if inferior else 'superior'} "
                                                          f"to {price_to_check}")
                        return True
                else:
                    if float(max(prices)) > price_to_check:
                        get_logger(self.get_name()).debug(f"{self.symbol} last prices: {prices}, "
                                                          f"ask for {'inferior' if inferior else 'superior'} "
                                                          f"to {price_to_check}")
                        return True
        return False

    async def cancel_order(self):
        self.status = OrderStatus.CANCELED
        self.canceled_time = time.time()

        cancelled_order = None

        # if real order
        if not self.trader.simulate and not self.is_self_managed():
            cancelled_order = await self.exchange_manager.exchange.cancel_order(self.order_id, self.symbol)

        await self.trader.notify_order_cancel(self)
        return cancelled_order

    async def cancel_from_exchange(self):
        self.status = OrderStatus.CANCELED
        self.canceled_time = time.time()
        await self.trader.notify_order_cancel(self)
        await self.trader.notify_order_close(self, cancel_linked_only=True)
        self.trader.get_order_manager().remove_order_from_list(self)

    async def close_order(self):
        await self.trader.notify_order_close(self)

    def get_currency_and_market(self) -> (str, str):
        return self.currency, self.market

    def get_total_fees(self, currency):
        if self.fee and self.fee[FeePropertyColumns.CURRENCY.value] == currency:
            return self.fee[FeePropertyColumns.COST.value]
        else:
            return 0

    def is_filled(self):
        return self.status == OrderStatus.FILLED

    def is_cancelled(self):
        return self.status == OrderStatus.CANCELED

    def get_computed_fee(self, forced_value=None):
        computed_fee = self.exchange_manager.exchange.get_trade_fee(self.symbol, self.order_type, self.filled_quantity,
                                                                    self.filled_price, self.taker_or_maker)
        return {
            FeePropertyColumns.COST.value:
                forced_value if forced_value is not None else computed_fee[FeePropertyColumns.COST.value],
            FeePropertyColumns.CURRENCY.value: computed_fee[FeePropertyColumns.CURRENCY.value],
        }

    def get_profitability(self):
        if self.filled_price != 0 and self.created_last_price != 0:
            if self.filled_price >= self.created_last_price:
                self.order_profitability = 1 - self.filled_price / self.created_last_price
                if self.side == TradeOrderSide.SELL:
                    self.order_profitability *= -1
            else:
                self.order_profitability = 1 - self.created_last_price / self.filled_price
                if self.side == TradeOrderSide.BUY:
                    self.order_profitability *= -1
        return self.order_profitability

    async def default_exchange_update_order_status(self):
        result = await self.exchange_manager.exchange.get_order(self.order_id, self.symbol)
        new_status = self.trader.parse_status(result)
        if new_status == OrderStatus.FILLED:
            self.trader.parse_exchange_order_to_trade_instance(result, self)
        elif new_status == OrderStatus.CANCELED:
            await self.cancel_from_exchange()

    def generate_executed_time(self, simulated_time=False):
        if not simulated_time or not self.last_prices:  # TODO
            return time.time()
        else:
            return self.last_prices[-1][ECOC.TIMESTAMP.value]

    def is_self_managed(self):
        # stop losses and take profits are self managed by the bot
        if self.order_type in [TraderOrderType.TAKE_PROFIT,
                               TraderOrderType.TAKE_PROFIT_LIMIT,
                               TraderOrderType.STOP_LOSS,
                               TraderOrderType.STOP_LOSS_LIMIT]:
            return True
        return False

    def update_from_raw(self, raw_order):
        if self.side is None or self.order_type is None:
            try:
                self.__update_type_from_raw(raw_order)
                if self.taker_or_maker is None:
                    self.__update_taker_maker_from_raw()
            except KeyError:
                pass

        return self.update(**{
            "symbol": get_value_or_default(raw_order, ExchangeConstantsOrderColumns.SYMBOL.value, None),
            "current_price": get_value_or_default(raw_order, ExchangeConstantsOrderColumns.PRICE.value, None),
            "quantity": get_value_or_default(raw_order, ExchangeConstantsOrderColumns.AMOUNT.value, None),
            "price": get_value_or_default(raw_order, ExchangeConstantsOrderColumns.PRICE.value, None),
            "stop_price": None,
            "status": Order.parse_order_status(raw_order),
            "order_id": get_value_or_default(raw_order, ExchangeConstantsOrderColumns.ID.value, None),
            "quantity_filled": get_value_or_default(raw_order, ExchangeConstantsOrderColumns.FILLED.value, None),
            "filled_price": get_value_or_default(raw_order, ExchangeConstantsOrderColumns.PRICE.value, None),
            "total_cost": get_value_or_default(raw_order, ExchangeConstantsOrderColumns.COST.value, None),
            "fee": get_value_or_default(raw_order, ExchangeConstantsOrderColumns.FEE.value, None),
            "timestamp": get_value_or_default(raw_order, ExchangeConstantsOrderColumns.TIMESTAMP.value, None)
        })

    @staticmethod
    def parse_order_type(raw_order):
        side: TradeOrderSide = TradeOrderSide(raw_order[ExchangeConstantsOrderColumns.SIDE.value])
        order_type: TradeOrderType = TradeOrderType(raw_order[ExchangeConstantsOrderColumns.TYPE.value])

        if side == TradeOrderSide.BUY:
            if order_type == TradeOrderType.LIMIT:
                order_type = TraderOrderType.BUY_LIMIT
            elif order_type == TradeOrderType.MARKET:
                order_type = TraderOrderType.BUY_MARKET
        elif side == TradeOrderSide.SELL:
            if order_type == TradeOrderType.LIMIT:
                order_type = TraderOrderType.SELL_LIMIT
            elif order_type == TradeOrderType.MARKET:
                order_type = TraderOrderType.SELL_MARKET
        return side, order_type

    @staticmethod
    def parse_order_status(raw_order):
        try:
            return OrderStatus(raw_order[ExchangeConstantsOrderColumns.STATUS.value])
        except KeyError:
            return None

    def update_order_from_raw(self, raw_order):
        self.status = Order.parse_order_status(raw_order)
        self.total_cost = raw_order[ExchangeConstantsOrderColumns.COST.value]
        self.filled_quantity = raw_order[ExchangeConstantsOrderColumns.FILLED.value]
        self.filled_price = raw_order[ExchangeConstantsOrderColumns.PRICE.value]
        if not self.filled_price and self.filled_quantity:
            self.filled_price = self.total_cost / self.filled_quantity
        self.taker_or_maker = Order.parse_order_type(raw_order)
        self.fee = raw_order[ExchangeConstantsOrderColumns.FEE.value]

        self.executed_time = self.trader.exchange.get_uniform_timestamp(
            raw_order[ExchangeConstantsOrderColumns.TIMESTAMP.value])

    def __update_type_from_raw(self, raw_order):
        self.side, self.order_type = Order.parse_order_type(raw_order)

    def __update_taker_maker_from_raw(self):
        if self.order_type in [TraderOrderType.SELL_MARKET, TraderOrderType.BUY_MARKET, TraderOrderType.STOP_LOSS]:
            # always true
            self.taker_or_maker = ExchangeConstantsMarketPropertyColumns.TAKER.value
        else:
            # true 90% of the time: impossible to know for sure the reality
            # (should only be used for simulation anyway)
            self.taker_or_maker = ExchangeConstantsMarketPropertyColumns.MAKER.value

    def to_string(self):
        return (f"{self.symbol} | "
                f"{self.order_type.name} | "
                f"Price : {self.origin_price} | "
                f"Quantity : {self.origin_quantity} | "
                f"Status : {self.status.name}")
