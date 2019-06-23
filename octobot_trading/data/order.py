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
from typing import Tuple

import math
from octobot_commons.logging.logging_util import get_logger
from octobot_commons.symbol_util import split_symbol

from octobot_trading.enums import TradeOrderSide, OrderStatus, TraderOrderType, \
    FeePropertyColumns, ExchangeConstantsMarketPropertyColumns, \
    ExchangeConstantsOrderColumns as ECOC

""" Order class will represent an open order in the specified exchange
In simulation it will also define rules to be filled / canceled
It is also use to store creation & fill values of the order """


class Order:

    def __init__(self, trader):
        self.trader = trader
        self.status = OrderStatus.OPEN
        self.creation_time = time.time()
        self.lock = Lock()
        self.linked_orders = []

        self.order_id = None
        self.symbol = None
        self.currency = None
        self.market = None
        self.order_notifier = None
        self.timestamp = None
        self.origin_price = None
        self.created_last_price = None
        self.origin_quantity = None
        self.origin_stop_price = None
        self.order_type = None
        self.filled_quantity = None
        self.linked_portfolio = None
        self.linked_to = None

    def update(self, order_type, symbol, currency, market,
               current_price, quantity, price, stop_price, status,
               order_notifier, order_id, quantity_filled,
               timestamp=None, linked_to=None, linked_portfolio=None):
        changed: bool = False

        if order_id and self.order_id != order_id:
            self.order_id = order_id

        if symbol and self.symbol != symbol:
            self.symbol, self.currency, self.market = symbol, currency, market

        if order_notifier:
            self.order_notifier = order_notifier

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
                self.creation_time = self.exchange.get_uniform_timestamp(timestamp)
            self.timestamp = self.creation_time

        if price and self.origin_price != price:
            self.origin_price = price
            changed = True

        if current_price and self.created_last_price != current_price:
            self.created_last_price = current_price
            changed = True

        if quantity and self.origin_quantity != quantity:
            self.origin_quantity = quantity
            changed = True

        if stop_price and self.origin_stop_price != stop_price:
            self.origin_stop_price = stop_price
            changed = True

        if order_type and self.order_type != order_type:
            self.order_type = order_type
            changed = True

        if self.trader.simulate:
            if quantity and self.filled_quantity != quantity:
                self.filled_quantity = quantity
                changed = True
        else:
            if quantity_filled and self.filled_quantity != quantity_filled:
                self.filled_quantity = quantity_filled
                changed = True

        if linked_to:
            self.linked_to = linked_to

        if linked_portfolio:
            self.linked_portfolio = linked_portfolio

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

        # if real order
        if not self.is_simulated and not self.trader.check_if_self_managed(self.order_type):
            await self.exchange.cancel_order(self.order_id, self.symbol)

        await self.trader.notify_order_cancel(self)

    async def cancel_from_exchange(self):
        self.status = OrderStatus.CANCELED
        self.canceled_time = time.time()
        await self.trader.notify_order_cancel(self)
        await self.trader.notify_order_close(self, cancel_linked_only=True)
        self.trader.get_order_manager().remove_order_from_list(self)

    async def close_order(self):
        await self.trader.notify_order_close(self)

    def get_currency_and_market(self) -> Tuple[str, str]:
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

    def get_string_info(self):
        return (f"{self.symbol} | "
                f"{self.order_type.name} | "
                f"Price : {self.origin_price} | "
                f"Quantity : {self.origin_quantity} | "
                f"Status : {self.status.name}")

    def get_description(self):
        return f"{self.order_id}{self.exchange.get_name()}{self.get_string_info()}"

    def matches_description(self, description):
        return self.get_description() == description

    def infer_taker_or_maker(self):
        if self.taker_or_maker is None:
            if self.order_type == TraderOrderType.SELL_MARKET \
                    or self.order_type == TraderOrderType.BUY_MARKET \
                    or self.order_type == TraderOrderType.STOP_LOSS:
                # always true
                return ExchangeConstantsMarketPropertyColumns.TAKER.value
            else:
                # true 90% of the time: impossible to know for sure the reality
                # (should only be used for simulation anyway)
                return ExchangeConstantsMarketPropertyColumns.MAKER.value
        return self.taker_or_maker

    def get_computed_fee(self, forced_value=None):
        computed_fee = self.exchange.get_trade_fee(self.symbol, self.order_type, self.filled_quantity,
                                                   self.filled_price, self.infer_taker_or_maker())
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

    @classmethod
    def get_name(cls):
        return cls.__name__

    async def default_exchange_update_order_status(self):
        result = await self.exchange.get_order(self.order_id, self.symbol)
        new_status = self.trader.parse_status(result)
        if new_status == OrderStatus.FILLED:
            self.trader.parse_exchange_order_to_trade_instance(result, self)
        elif new_status == OrderStatus.CANCELED:
            await self.cancel_from_exchange()

    def generate_executed_time(self, simulated_time=False):
        if not simulated_time or not self.last_prices:
            return time.time()
        else:
            return self.last_prices[-1][ECOC.TIMESTAMP.value]
