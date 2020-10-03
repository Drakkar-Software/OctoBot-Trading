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
import asyncio

import typing

import octobot_commons.logging as logging

import octobot_trading.enums as enums
import octobot_trading.personal_data as personal_data
import octobot_trading.util as util


class Order(util.Initializable):
    """
    Order class will represent an open order in the specified exchange
    In simulation it will also define rules to be filled / canceled
    It is also use to store creation & fill values of the order
    """
    CHECK_ORDER_STATUS_AFTER_INIT_DELAY = 2

    def __init__(self, trader, side=None):
        super().__init__()
        self.trader = trader
        self.exchange_manager = trader.exchange_manager
        self.status = enums.OrderStatus.OPEN
        self.creation_time = self.exchange_manager.exchange.get_exchange_current_time()
        self.executed_time = 0
        self.lock = asyncio.Lock()
        self.linked_orders = []

        self.is_synchronized_with_exchange = False
        self.is_from_this_octobot = True
        self.order_id = trader.parse_order_id(None)
        self.simulated = trader.simulate

        self.logger_name = None
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
        self.side = side
        self.filled_quantity = 0
        self.linked_portfolio = None
        self.linked_to = None
        self.canceled_time = 0
        self.fee = None
        self.filled_price = 0
        self.order_profitability = 0
        self.total_cost = 0

        # raw exchange order type, used to create order dict
        self.exchange_order_type = None

        # order state is initialized in initialize_impl()
        self.state = None

    @classmethod
    def get_name(cls):
        return cls.__name__

    def get_logger_name(self):
        if self.logger_name is None:
            self.logger_name = f"{self.get_name()} | {self.order_id}"
        return self.logger_name

    def update(self, symbol, order_id="", status=enums.OrderStatus.OPEN,
               current_price=0.0, quantity=0.0, price=0.0, stop_price=0.0,
               quantity_filled=0.0, filled_price=0.0, average_price=0.0, fee=None, total_cost=0.0,
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
            self.status = enums.OrderStatus.OPEN

        if timestamp and self.timestamp != timestamp:
            self.timestamp = timestamp
        if not self.timestamp:
            if not timestamp:
                self.creation_time = self.exchange_manager.exchange.get_exchange_current_time()
            else:
                # if we have a timestamp, it's a real trader => need to format timestamp if necessary
                self.creation_time = self.exchange_manager.exchange.get_uniform_timestamp(timestamp)
            self.timestamp = self.creation_time

        if status in {enums.OrderStatus.FILLED, enums.OrderStatus.CLOSED} and not self.executed_time:
            self.executed_time = self.timestamp

        if price and self.origin_price != price:
            self.origin_price = price
            changed = True

        if fee is not None and self.fee != fee:
            self.fee = fee

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

        if average_price:
            # try using average price first
            if self.filled_price != average_price:
                self.filled_price = average_price
        else:
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
            if self.exchange_order_type is None:
                self.exchange_order_type = _get_trade_order_type(order_type)

        if not self.filled_price and self.filled_quantity and self.total_cost:
            self.filled_price = self.total_cost / self.filled_quantity
            if timestamp is not None:
                self.executed_time = self.exchange_manager.exchange.get_uniform_timestamp(timestamp)

        if self.taker_or_maker is None:
            self._update_taker_maker()
        return changed

    async def initialize_impl(self, **kwargs):
        """
        Initialize order status update tasks
        """
        await personal_data.create_order_state(self, **kwargs)
        if not self.is_closed():
            await self.update_order_status()

    async def update_order_status(self, force_refresh=False):
        """
        Update_order_status will define the rules for a simulated order to be filled / canceled
        """
        raise NotImplementedError("Update_order_status not implemented")

    def add_linked_order(self, order):
        self.linked_orders.append(order)

    def get_currency_and_market(self) -> (str, str):
        return self.currency, self.market

    def get_total_fees(self, currency):
        return personal_data.get_fees_for_currency(self.fee, currency)

    def is_open(self):
        return self.state is None or self.state.is_open()

    def is_filled(self):
        return self.state.is_filled() or (self.state.is_closed() and self.status is enums.OrderStatus.FILLED)

    def is_cancelled(self):
        return self.state.is_canceled() or (self.state.is_closed() and self.status is enums.OrderStatus.CANCELED)

    def is_closed(self):
        return self.state.is_closed() if self.state is not None else self.status == enums.OrderStatus.CLOSED

    async def on_open(self, force_open=False, is_from_exchange_data=False):
        self.state = personal_data.OpenOrderState(self, is_from_exchange_data=is_from_exchange_data)
        await self.state.initialize(forced=force_open)

    async def on_fill(self, force_fill=False, is_from_exchange_data=False):
        if self.is_open():
            self.state = personal_data.FillOrderState(self, is_from_exchange_data=is_from_exchange_data)
            await self.state.initialize(forced=force_fill)
        else:
            logging.get_logger(self.get_logger_name()).debug(f"Trying to fill a previously filled or canceled order: "
                                                             f"ignored fill call for {self}")

    async def on_close(self, force_close=False, is_from_exchange_data=False):
        self.state = personal_data.CloseOrderState(self, is_from_exchange_data=is_from_exchange_data)
        await self.state.initialize(forced=force_close)

    async def on_cancel(self, is_from_exchange_data=False, force_cancel=False, ignored_order=None):
        self.state = personal_data.CancelOrderState(self, is_from_exchange_data=is_from_exchange_data)
        await self.state.initialize(forced=force_cancel, ignored_order=ignored_order)

    def on_fill_actions(self):
        """
        Perform on_fill actions
        """
        self.status = enums.OrderStatus.FILLED

    async def on_filled(self):
        """
        Filling complete callback
        """
        # nothing to do by default

    def get_computed_fee(self, forced_value=None):
        computed_fee = self.exchange_manager.exchange.get_trade_fee(self.symbol, self.order_type, self.filled_quantity,
                                                                    self.filled_price, self.taker_or_maker)
        return {
            enums.FeePropertyColumns.COST.value:
                forced_value if forced_value is not None else computed_fee[enums.FeePropertyColumns.COST.value],
            enums.FeePropertyColumns.CURRENCY.value: computed_fee[enums.FeePropertyColumns.CURRENCY.value],
        }

    def get_profitability(self):
        if self.filled_price != 0 and self.created_last_price != 0:
            if self.filled_price >= self.created_last_price:
                self.order_profitability = 1 - self.filled_price / self.created_last_price
                if self.side is enums.TradeOrderSide.SELL:
                    self.order_profitability *= -1
            else:
                self.order_profitability = 1 - self.created_last_price / self.filled_price
                if self.side is enums.TradeOrderSide.BUY:
                    self.order_profitability *= -1
        return self.order_profitability

    async def default_exchange_update_order_status(self):
        result = await self.exchange_manager.exchange.get_order(self.order_id, self.symbol)
        new_status = self.trader.parse_status(result)
        self.is_synchronized_with_exchange = True
        if new_status in {enums.OrderStatus.FILLED, enums.OrderStatus.CLOSED}:
            await self.on_fill()
        elif new_status is enums.OrderStatus.CANCELED:
            await self.trader.cancel_order(self)

    def generate_executed_time(self):
        return self.exchange_manager.exchange.get_exchange_current_time()

    def is_self_managed(self):
        # stop losses and take profits are self managed by the bot
        if self.order_type in [enums.TraderOrderType.TAKE_PROFIT,
                               enums.TraderOrderType.TAKE_PROFIT_LIMIT,
                               enums.TraderOrderType.STOP_LOSS,
                               enums.TraderOrderType.STOP_LOSS_LIMIT,
                               enums.TraderOrderType.TRAILING_STOP,
                               enums.TraderOrderType.TRAILING_STOP_LIMIT]:
            return True
        return False

    def update_from_raw(self, raw_order):
        if self.side is None or self.order_type is None:
            try:
                self._update_type_from_raw(raw_order)
                if self.taker_or_maker is None:
                    self._update_taker_maker()
            except KeyError:
                logging.get_logger(self.__class__.__name__).warning("Failed to parse order side and type")

        filled_price = raw_order.get(enums.ExchangeConstantsOrderColumns.PRICE.value, 0.0)
        # set average price with real average price if available, use filled_price otherwise
        average_price = raw_order.get(enums.ExchangeConstantsOrderColumns.AVERAGE.value, 0.0) or filled_price

        return self.update(
            symbol=str(raw_order.get(enums.ExchangeConstantsOrderColumns.SYMBOL.value, None)),
            current_price=raw_order.get(enums.ExchangeConstantsOrderColumns.PRICE.value, 0.0),
            quantity=raw_order.get(enums.ExchangeConstantsOrderColumns.AMOUNT.value, 0.0),
            price=raw_order.get(enums.ExchangeConstantsOrderColumns.PRICE.value, 0.0),
            status=personal_data.parse_order_status(raw_order),
            order_id=str(raw_order.get(enums.ExchangeConstantsOrderColumns.ID.value, None)),
            quantity_filled=raw_order.get(enums.ExchangeConstantsOrderColumns.FILLED.value, 0.0),
            filled_price=filled_price,
            average_price=average_price,
            total_cost=raw_order.get(enums.ExchangeConstantsOrderColumns.COST.value, 0.0),
            fee=raw_order.get(enums.ExchangeConstantsOrderColumns.FEE.value, None),
            timestamp=raw_order.get(enums.ExchangeConstantsOrderColumns.TIMESTAMP.value, None)
        )

    def consider_as_filled(self):
        self.status = enums.OrderStatus.FILLED
        if self.executed_time == 0:
            self.executed_time = self.timestamp
        if self.filled_quantity == 0:
            self.filled_quantity = self.origin_quantity
        if self.filled_price == 0:
            self.filled_price = self.origin_price

    def update_order_from_raw(self, raw_order):
        self.status = personal_data.parse_order_status(raw_order)
        self.total_cost = raw_order[enums.ExchangeConstantsOrderColumns.COST.value]
        self.filled_quantity = raw_order[enums.ExchangeConstantsOrderColumns.FILLED.value]
        self.filled_price = raw_order[enums.ExchangeConstantsOrderColumns.PRICE.value]
        if not self.filled_price and self.filled_quantity:
            self.filled_price = self.total_cost / self.filled_quantity

        self._update_taker_maker()

        self.fee = raw_order[enums.ExchangeConstantsOrderColumns.FEE.value]

        self.executed_time = self.trader.exchange.get_uniform_timestamp(
            raw_order[enums.ExchangeConstantsOrderColumns.TIMESTAMP.value])

    def _update_type_from_raw(self, raw_order):
        try:
            self.exchange_order_type = enums.TradeOrderType(raw_order[enums.ExchangeConstantsOrderColumns.TYPE.value])
        except ValueError:
            self.exchange_order_type = enums.TradeOrderType.UNKNOWN
        self.side, self.order_type = parse_order_type(raw_order)

    def _update_taker_maker(self):
        if self.order_type in [enums.TraderOrderType.SELL_MARKET,
                               enums.TraderOrderType.BUY_MARKET,
                               enums.TraderOrderType.STOP_LOSS]:
            # always true
            self.taker_or_maker = enums.ExchangeConstantsMarketPropertyColumns.TAKER.value
        else:
            # true 90% of the time: impossible to know for sure the reality
            # (should only be used for simulation anyway)
            self.taker_or_maker = enums.ExchangeConstantsMarketPropertyColumns.MAKER.value

    def to_dict(self):
        filled_price = self.filled_price if self.filled_price > 0 else self.origin_price
        return {
            enums.ExchangeConstantsOrderColumns.ID.value: self.order_id,
            enums.ExchangeConstantsOrderColumns.SYMBOL.value: self.symbol,
            enums.ExchangeConstantsOrderColumns.PRICE.value: filled_price,
            enums.ExchangeConstantsOrderColumns.STATUS.value: self.status.value,
            enums.ExchangeConstantsOrderColumns.TIMESTAMP.value: self.timestamp,
            enums.ExchangeConstantsOrderColumns.TYPE.value: self.exchange_order_type.value
            if self.exchange_order_type else None,
            enums.ExchangeConstantsOrderColumns.SIDE.value: self.side.value,
            enums.ExchangeConstantsOrderColumns.AMOUNT.value: self.origin_quantity,
            enums.ExchangeConstantsOrderColumns.COST.value: self.total_cost,
            enums.ExchangeConstantsOrderColumns.FILLED.value: self.filled_quantity,
            enums.ExchangeConstantsOrderColumns.FEE.value: self.fee
        }

    def clear(self):
        self.state.clear()
        self.trader = None
        self.exchange_manager = None
        self.linked_to = None
        self.linked_portfolio = None
        self.linked_orders = []

    def to_string(self):
        return (f"{self.symbol} | "
                f"{self.order_type.name if self.order_type is not None else 'Unknown'} | "
                f"Price : {self.origin_price} | "
                f"Quantity : {self.origin_quantity} | "
                f"State : {self.state.state.value if self.state is not None else 'Unknown'} | "
                f"id : {self.order_id}")

    def __str__(self):
        return self.to_string()

    def is_to_be_maintained(self):
        return self.trader is not None


def parse_order_type(raw_order):
    try:
        side: enums.TradeOrderSide = enums.TradeOrderSide(raw_order[enums.ExchangeConstantsOrderColumns.SIDE.value])
        order_type: enums.TradeOrderType = enums.TradeOrderType.UNKNOWN
        parsed_order_type: enums.TraderOrderType = enums.TraderOrderType.UNKNOWN
        try:
            order_type = enums.TradeOrderType(raw_order[enums.ExchangeConstantsOrderColumns.TYPE.value])
        except ValueError as e:
            if raw_order[enums.ExchangeConstantsOrderColumns.TYPE.value] is None:
                # No order type info: use unknown order type
                return side, enums.TraderOrderType.UNKNOWN
            else:
                # Incompatible order type info: raise error
                raise e

        if order_type == enums.TradeOrderType.UNKNOWN:
            parsed_order_type = enums.TraderOrderType.UNKNOWN
        elif side == enums.TradeOrderSide.BUY:
            if order_type == enums.TradeOrderType.LIMIT or order_type == enums.TradeOrderType.LIMIT_MAKER:
                parsed_order_type = enums.TraderOrderType.BUY_LIMIT
            elif order_type == enums.TradeOrderType.MARKET:
                parsed_order_type = enums.TraderOrderType.BUY_MARKET
            else:
                parsed_order_type = _get_sell_and_buy_types(order_type)
        elif side == enums.TradeOrderSide.SELL:
            if order_type == enums.TradeOrderType.LIMIT or order_type == enums.TradeOrderType.LIMIT_MAKER:
                parsed_order_type = enums.TraderOrderType.SELL_LIMIT
            elif order_type == enums.TradeOrderType.MARKET:
                parsed_order_type = enums.TraderOrderType.SELL_MARKET
            else:
                parsed_order_type = _get_sell_and_buy_types(order_type)
        return side, parsed_order_type
    except (KeyError, ValueError):
        return None, None


def _get_trade_order_type(order_type: enums.TraderOrderType) -> typing.Optional[enums.TradeOrderType]:
    if order_type == enums.TraderOrderType.BUY_LIMIT or order_type == enums.TraderOrderType.SELL_LIMIT:
        return enums.TradeOrderType.LIMIT
    if order_type == enums.TraderOrderType.BUY_MARKET or order_type == enums.TraderOrderType.SELL_MARKET:
        return enums.TradeOrderType.MARKET
    elif order_type == enums.TraderOrderType.TAKE_PROFIT:
        return enums.TradeOrderType.TAKE_PROFIT
    elif order_type == enums.TraderOrderType.TAKE_PROFIT_LIMIT:
        return enums.TradeOrderType.TAKE_PROFIT_LIMIT
    elif order_type == enums.TraderOrderType.STOP_LOSS:
        return enums.TradeOrderType.STOP_LOSS
    elif order_type == enums.TraderOrderType.STOP_LOSS_LIMIT:
        return enums.TradeOrderType.STOP_LOSS_LIMIT
    elif order_type == enums.TraderOrderType.TRAILING_STOP:
        return enums.TradeOrderType.TRAILING_STOP
    elif order_type == enums.TraderOrderType.TRAILING_STOP_LIMIT:
        return enums.TradeOrderType.TRAILING_STOP_LIMIT
    return None


def _get_sell_and_buy_types(order_type) -> typing.Optional[enums.TraderOrderType]:
    if order_type == enums.TradeOrderType.STOP_LOSS:
        return enums.TraderOrderType.STOP_LOSS
    elif order_type == enums.TradeOrderType.STOP_LOSS_LIMIT:
        return enums.TraderOrderType.STOP_LOSS_LIMIT
    elif order_type == enums.TradeOrderType.TAKE_PROFIT:
        return enums.TraderOrderType.TAKE_PROFIT
    elif order_type == enums.TradeOrderType.TAKE_PROFIT_LIMIT:
        return enums.TraderOrderType.TAKE_PROFIT_LIMIT
    elif order_type == enums.TradeOrderType.TRAILING_STOP:
        return enums.TraderOrderType.TRAILING_STOP
    elif order_type == enums.TradeOrderType.TRAILING_STOP_LIMIT:
        return enums.TraderOrderType.TRAILING_STOP_LIMIT
    return None
