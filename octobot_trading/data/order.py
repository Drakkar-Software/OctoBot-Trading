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
from asyncio import Lock

from octobot_commons.asyncio_tools import wait_asyncio_next_cycle
from octobot_commons.logging.logging_util import get_logger

from octobot_trading.channels.exchange_channel import get_chan
from octobot_trading.constants import ORDERS_CHANNEL
from octobot_trading.enums import TradeOrderSide, OrderStatus, TraderOrderType, \
    FeePropertyColumns, ExchangeConstantsMarketPropertyColumns, \
    ExchangeConstantsOrderColumns, TradeOrderType
from octobot_trading.orders.order_util import get_fees_for_currency
from octobot_trading.util.initializable import Initializable


class Order(Initializable):
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
        self.status = OrderStatus.OPEN
        self.creation_time = self.exchange_manager.exchange.get_exchange_current_time()
        self.executed_time = 0
        self.lock = Lock()
        self.linked_orders = []

        self.is_synchronized_with_exchange = False
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

    @classmethod
    def get_name(cls):
        return cls.__name__

    def get_logger_name(self):
        if self.logger_name is None:
            self.logger_name = f"{self.get_name()} | {self.order_id}"
        return self.logger_name

    def update(self, symbol, order_id="", status=OrderStatus.OPEN,
               current_price=0.0, quantity=0.0, price=0.0, stop_price=0.0,
               quantity_filled=0.0, filled_price=0.0, fee=None, total_cost=0.0,
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
                self.creation_time = self.exchange_manager.exchange.get_exchange_current_time()
            else:
                # if we have a timestamp, it's a real trader => need to format timestamp if necessary
                self.creation_time = self.exchange_manager.exchange.get_uniform_timestamp(timestamp)
            self.timestamp = self.creation_time

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
        return changed

    async def initialize_impl(self):
        """
        Initialize order status update tasks
        """
        if not self.exchange_manager.is_backtesting:
            asyncio.get_event_loop().call_later(self.CHECK_ORDER_STATUS_AFTER_INIT_DELAY,
                                                asyncio.create_task,
                                                self.update_order_status())
        else:
            # In backtesting wait for the next asyncio loop iteration to ensure this order status
            # is updated before leaving this method
            asyncio.create_task(self.update_order_status())
            await wait_asyncio_next_cycle()

    async def update_order_status(self, force_refresh=False):
        """
        Update_order_status will define the rules for a simulated order to be filled / canceled
        """
        raise NotImplementedError("Update_order_status not implemented")

    def cancel_order(self):
        """
        Set cancelled status and keep track of cancellation time.
        """
        self.status = OrderStatus.CANCELED
        self.canceled_time = self.exchange_manager.exchange.get_exchange_current_time()

    async def on_fill(self):
        """
        Set filled status
        """
        self.status = OrderStatus.FILLED
        self.executed_time = self.generate_executed_time()

    async def on_fill_complete(self):
        """
        Post fill actions
        """
        try:
            # compute order fees
            self.fee = self.get_computed_fee()

            get_logger(self.get_logger_name()).debug(f"{self.symbol} of size {self.origin_quantity} {self.currency} "
                                                     f"filled {self.filled_quantity} {self.currency} "
                                                     f"on {self.exchange_manager.exchange_name} "
                                                     f"at {self.filled_price}")

            await get_chan(ORDERS_CHANNEL, self.exchange_manager.id).get_internal_producer() \
                .send(cryptocurrency=self.currency,
                      symbol=self.symbol,
                      order=self.to_dict(),
                      is_from_bot=True,
                      is_closed=True,
                      is_updated=False)
            await self.exchange_manager.trader.close_filled_order(self)
        except Exception as e:
            get_logger(self.get_logger_name()).exception(e, True, f"Fail to execute fill complete action : {e}.")

    def add_linked_order(self, order):
        self.linked_orders.append(order)

    def get_currency_and_market(self) -> (str, str):
        return self.currency, self.market

    def get_total_fees(self, currency):
        return get_fees_for_currency(self.fee, currency)

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
        self.is_synchronized_with_exchange = True
        if new_status == OrderStatus.FILLED:
            self.trader.parse_exchange_order_to_trade_instance(result, self)
        elif new_status == OrderStatus.CANCELED:
            await self.trader.cancel_order(self)

    def generate_executed_time(self):
        return self.exchange_manager.exchange.get_exchange_current_time()

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
                get_logger(self.__class__.__name__).warning("Failed to parse order side and type")

        return self.update(
            symbol=str(raw_order.get(ExchangeConstantsOrderColumns.SYMBOL.value, None)),
            current_price=raw_order.get(ExchangeConstantsOrderColumns.PRICE.value, 0.0),
            quantity=raw_order.get(ExchangeConstantsOrderColumns.AMOUNT.value, 0.0),
            price=raw_order.get(ExchangeConstantsOrderColumns.PRICE.value, 0.0),
            status=parse_order_status(raw_order),
            order_id=str(raw_order.get(ExchangeConstantsOrderColumns.ID.value, None)),
            quantity_filled=raw_order.get(ExchangeConstantsOrderColumns.FILLED.value, 0.0),
            filled_price=raw_order.get(ExchangeConstantsOrderColumns.PRICE.value, 0.0),
            total_cost=raw_order.get(ExchangeConstantsOrderColumns.COST.value, 0.0),
            fee=raw_order.get(ExchangeConstantsOrderColumns.FEE.value, None),
            timestamp=raw_order.get(ExchangeConstantsOrderColumns.TIMESTAMP.value, None)
        )

    def consider_as_filled(self):
        self.status = OrderStatus.FILLED
        if self.executed_time == 0:
            self.executed_time = self.timestamp
        if self.filled_quantity == 0:
            self.filled_quantity = self.origin_quantity
        if self.filled_price == 0:
            self.filled_price = self.origin_price

    def update_order_from_raw(self, raw_order):
        self.status = parse_order_status(raw_order)
        self.total_cost = raw_order[ExchangeConstantsOrderColumns.COST.value]
        self.filled_quantity = raw_order[ExchangeConstantsOrderColumns.FILLED.value]
        self.filled_price = raw_order[ExchangeConstantsOrderColumns.PRICE.value]
        if not self.filled_price and self.filled_quantity:
            self.filled_price = self.total_cost / self.filled_quantity

        self.__update_taker_maker_from_raw()

        self.fee = raw_order[ExchangeConstantsOrderColumns.FEE.value]

        self.executed_time = self.trader.exchange.get_uniform_timestamp(
            raw_order[ExchangeConstantsOrderColumns.TIMESTAMP.value])

    def __update_type_from_raw(self, raw_order):
        try:
            self.exchange_order_type = TradeOrderType(raw_order[ExchangeConstantsOrderColumns.TYPE.value])
        except ValueError:
            self.exchange_order_type = TradeOrderType.UNKNOWN
        self.side, self.order_type = parse_order_type(raw_order)

    def __update_taker_maker_from_raw(self):
        if self.order_type in [TraderOrderType.SELL_MARKET, TraderOrderType.BUY_MARKET, TraderOrderType.STOP_LOSS]:
            # always true
            self.taker_or_maker = ExchangeConstantsMarketPropertyColumns.TAKER.value
        else:
            # true 90% of the time: impossible to know for sure the reality
            # (should only be used for simulation anyway)
            self.taker_or_maker = ExchangeConstantsMarketPropertyColumns.MAKER.value

    def to_dict(self):
        filled_price = self.filled_price if self.filled_price > 0 else self.origin_price
        return {
            ExchangeConstantsOrderColumns.ID.value: self.order_id,
            ExchangeConstantsOrderColumns.SYMBOL.value: self.symbol,
            ExchangeConstantsOrderColumns.PRICE.value: filled_price,
            ExchangeConstantsOrderColumns.STATUS.value: self.status.value,
            ExchangeConstantsOrderColumns.TIMESTAMP.value: self.timestamp,
            ExchangeConstantsOrderColumns.TYPE.value: self.exchange_order_type.value,
            ExchangeConstantsOrderColumns.SIDE.value: self.side.value,
            ExchangeConstantsOrderColumns.AMOUNT.value: self.origin_quantity,
            ExchangeConstantsOrderColumns.COST.value: self.total_cost,
            ExchangeConstantsOrderColumns.FILLED.value: self.filled_quantity,
            ExchangeConstantsOrderColumns.FEE.value: self.fee
        }

    def clear(self):
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
                f"Status : {self.status.name if self.status is not None else 'Unknown'}")

    def __str__(self):
        return self.to_string()


def parse_order_type(raw_order):
    try:
        side: TradeOrderSide = TradeOrderSide(raw_order[ExchangeConstantsOrderColumns.SIDE.value])
        order_type: TradeOrderType = TradeOrderType.UNKNOWN
        parsed_order_type: TraderOrderType = TraderOrderType.UNKNOWN
        try:
            order_type = TradeOrderType(raw_order[ExchangeConstantsOrderColumns.TYPE.value])
        except ValueError as e:
            if raw_order[ExchangeConstantsOrderColumns.TYPE.value] is None:
                # No order type info: use unknown order type
                return side, TraderOrderType.UNKNOWN
            else:
                # Incompatible order type info: raise error
                raise e

        if order_type == TradeOrderType.UNKNOWN:
            parsed_order_type = TraderOrderType.UNKNOWN
        elif side == TradeOrderSide.BUY:
            if order_type == TradeOrderType.LIMIT or order_type == TradeOrderType.LIMIT_MAKER:
                parsed_order_type = TraderOrderType.BUY_LIMIT
            elif order_type == TradeOrderType.MARKET:
                parsed_order_type = TraderOrderType.BUY_MARKET
            else:
                parsed_order_type = _get_sell_and_buy_types(order_type)
        elif side == TradeOrderSide.SELL:
            if order_type == TradeOrderType.LIMIT or order_type == TradeOrderType.LIMIT_MAKER:
                parsed_order_type = TraderOrderType.SELL_LIMIT
            elif order_type == TradeOrderType.MARKET:
                parsed_order_type = TraderOrderType.SELL_MARKET
            else:
                parsed_order_type = _get_sell_and_buy_types(order_type)
        return side, parsed_order_type
    except (KeyError, ValueError):
        return None, None


def _get_trade_order_type(order_type: TraderOrderType) -> TradeOrderType:
    if order_type == TraderOrderType.BUY_LIMIT \
            or order_type == TraderOrderType.SELL_LIMIT:
        return TradeOrderType.LIMIT
    if order_type == TraderOrderType.BUY_MARKET \
            or order_type == TraderOrderType.SELL_MARKET:
        return TradeOrderType.MARKET
    elif order_type == TraderOrderType.STOP_LOSS_LIMIT:
        return TradeOrderType.STOP_LOSS_LIMIT
    elif order_type == TraderOrderType.TAKE_PROFIT_LIMIT:
        return TradeOrderType.TAKE_PROFIT_LIMIT
    elif order_type == TraderOrderType.TAKE_PROFIT:
        return TradeOrderType.TAKE_PROFIT
    elif order_type == TraderOrderType.STOP_LOSS:
        return TradeOrderType.STOP_LOSS
    return None


def _get_sell_and_buy_types(order_type) -> TraderOrderType:
    if order_type == TradeOrderType.STOP_LOSS:
        return TraderOrderType.STOP_LOSS
    elif order_type == TradeOrderType.STOP_LOSS_LIMIT:
        return TraderOrderType.STOP_LOSS_LIMIT
    elif order_type == TradeOrderType.TAKE_PROFIT:
        return TraderOrderType.TAKE_PROFIT
    elif order_type == TradeOrderType.TAKE_PROFIT_LIMIT:
        return TraderOrderType.TAKE_PROFIT_LIMIT
    return None


def parse_order_status(raw_order):
    try:
        return OrderStatus(raw_order[ExchangeConstantsOrderColumns.STATUS.value])
    except KeyError:
        return KeyError("Could not parse new order status")
