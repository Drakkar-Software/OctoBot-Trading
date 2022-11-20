import decimal
import typing
import cryptofeed.defines as cryptofeed_constants

from octobot_trading import constants
from octobot_trading.enums import (
    ExchangeConstantsFeesColumns,
    ExchangeConstantsOrderColumns as OrderCols,
    OrderStatus,
    TradeOrderSide,
    TraderOrderType,
)
from octobot_trading.enums import ExchangeConstantsMarketPropertyColumns as MarketCols
from octobot_trading.enums import TradeOrderType as TradeOrderType
from .util import Parser


class OrdersParser(Parser):
    """
    overwrite OrdersParser class methods if necessary
    always/only include bulletproof custom code into the parser to improve generic support

    parser usage:   parser = OrdersParser(exchange)
                    orders = await parser.parse_orders(raw_orders)
                    order = await parser.parse_order(raw_order)
    """

    def __init__(self, exchange):
        super().__init__(exchange=exchange)
        self.PARSER_TITLE = "orders"
        self.fetched_order = None

    async def parse_orders(
            self,
            raw_orders: list,
            order_type: str = None,
            quantity: decimal.Decimal = None,
            price: decimal.Decimal = None,
            status: str = None,
            symbol: str = None,
            side: str = None,
            timestamp: int or float = None,
            check_completeness: bool = True,
    ) -> list:
        """
        use this method to parse a raw list of orders

        :param raw_orders:

        optional:
        :param status: to use if it's missing in the order
        :param order_type: to use if it's missing in the order
        :param price: to use if it's missing in the order
        :param quantity: to use if it's missing in the order
        :param symbol: to use if it's missing in the order
        :param side: to use if it's missing in the order
        :param timestamp: to use if it's missing in the order

        :param check_completeness: if true checks all attributes,
            if somethings missing it'll try to fetch it from the exchange

        :return: formatted orders list of order dicts
        """
        check_completeness = (
            check_completeness if check_completeness is not None else True
        )
        self._ensure_list(raw_orders)
        # todo sort by time - some exchanges are reversed
        self.formatted_records = (
            [
                await self.parse_order(
                    raw_order,
                    order_type=order_type,
                    quantity=quantity,
                    price=price,
                    status=status,
                    symbol=symbol,
                    side=side,
                    timestamp=timestamp,
                    check_completeness=check_completeness,
                )
                for raw_order in raw_orders
            ]
            if self.raw_records
            else []
        )
        if check_completeness:
            self._create_debugging_report()
        return self.formatted_records

    async def parse_order(
            self,
            raw_order: dict,
            order_type: str = None,
            quantity: decimal.Decimal = None,
            price: decimal.Decimal = None,
            status: str = None,
            symbol: str = None,
            side: str = None,
            timestamp: int or float = None,
            check_completeness: bool = True,
    ) -> dict:
        """
        use this method to format a single order

        :param raw_order: raw order with eventually missing data

        optional:
        :param status: to use if it's missing in the order
        :param order_type: to use if it's missing in the order
        :param price: to use if it's missing in the order
        :param quantity: to use if it's missing in the order
        :param symbol: to use if it's missing in the order
        :param side: to use if it's missing in the order
        :param timestamp: to use if it's missing in the order

        :param check_completeness: if true checks all attributes,
            if somethings missing it'll try to fetch it from the exchange

        :return: formatted order dict (100% complete or we raise NotImplemented)

        """
        check_completeness = (
            check_completeness if check_completeness is not None else True
        )
        # todo post only
        self.fetched_order = None  # clear previous fetched order
        self._ensure_dict(raw_order)
        self._parse_id()
        self._parse_status(status)
        self._parse_timestamp(timestamp)
        self._parse_symbol(symbol)
        self._parse_side(side)
        self._parse_type(order_type)  # parse after side
        self._parse_taker_or_maker()  # parse after type
        self._parse_price(price)  # parse after type, status
        self._parse_filled_price()  # parse after price
        self._parse_average_price()
        self._parse_amount(quantity)
        self._parse_remaining()  # parse after amount and status
        self._parse_filled_amount()  # parse after amount and remaining
        self._parse_cost()
        self._parse_reduce_only()  # parse after type
        self._parse_tag()
        self._parse_fees()
        # self._parse_datetime(timestamp)  # remove? is it used?
        # self._parse_last_trade_timestamp()  # remove? is it used?
        # self._parse_quantity_currency()  # remove? is it used?

        if check_completeness:
            await self._fetch_if_missing()
            self._create_debugging_report_for_record()
        return self.formatted_record

    def _parse_status(self, missing_status_value):
        def missing_status():
            if missing_status_value:
                return missing_status_value
            self._log_missing(OrderCols.STATUS.value, OrderCols.STATUS.value)

        def found_status(raw_status):
            try:
                return OrderStatus(raw_status).value
            except ValueError:
                if order_status := try_cryptofeed_order_status(raw_status):
                    return order_status
                missing_status()

        self._try_to_find_and_parse_with_method(
            OrderCols.STATUS.value,
            [OrderCols.STATUS.value],
            parse_method=found_status,
            not_found_method=missing_status,
        )

    def _parse_id(self):
        self._try_to_find_and_set(OrderCols.ID.value, [OrderCols.ID.value])

    def _parse_timestamp(self, missing_timestamp_value):
        self._try_to_find_and_parse_with_method(
            OrderCols.TIMESTAMP.value,
            [OrderCols.TIMESTAMP.value],
            parse_method=self.found_timestamp,
            not_found_val=missing_timestamp_value,
            enable_log=False if missing_timestamp_value else True,
        )

    # def _parse_datetime(self, missing_timestamp_value):
    #     # todo is it even used?
    #     self._try_to_find_and_set(OrderCols.DATETIME.value, [OrderCols.DATETIME.value])

    # def _parse_last_trade_timestamp(self):
    #     # todo is this important?
    #     self._try_to_find_and_set(
    #         OrderCols.LAST_TRADE_TIMESTAMP.value,
    #         [OrderCols.LAST_TRADE_TIMESTAMP.value],
    #         enable_log=False,
    #     )

    # def _parse_quantity_currency(self):
    #     # todo is this important?
    #     self._try_to_find_and_set(
    #         OrderCols.QUANTITY_CURRENCY.value,
    #         [OrderCols.QUANTITY_CURRENCY.value],
    #         enable_log=False,
    #     )

    def _parse_symbol(self, missing_symbol):
        # todo convert to symbol object
        # symbol_util.parse_symbol()
        self._try_to_find_and_set(
            OrderCols.SYMBOL.value,
            [OrderCols.SYMBOL.value],
            not_found_val=missing_symbol,
            enable_log=False if missing_symbol else True,
        )

    def _parse_type(self, missing_type_value=None):
        def type_found(raw_order_type):
            self.handle_type_found(raw_order_type, missing_type_value)

        self._try_to_find_and_parse_with_method(
            OrderCols.OCTOBOT_ORDER_TYPE.value,
            [OrderCols.TYPE.value],
            parse_method=type_found,
            not_found_method=self.missing_type,
            enable_log=False,
        )

        # market orders with no price but with stop price are stop orders
        if self.raw_record.get(OrderCols.STOP_PRICE.value) and not self.raw_record.get(OrderCols.PRICE.value) \
                and self.formatted_record[OrderCols.TYPE.value] == TradeOrderType.MARKET.value:
            self.formatted_record[OrderCols.OCTOBOT_ORDER_TYPE.value] = TraderOrderType.STOP_LOSS.value
            self.formatted_record[OrderCols.TYPE.value] = TradeOrderType.STOP_LOSS.value

    def _parse_side(self, missing_side_value):
        self._try_to_find_and_parse_with_method(
            OrderCols.SIDE.value,
            [OrderCols.SIDE.value],
            parse_method=found_side,
            not_found_val=missing_side_value,
            enable_log=False if missing_side_value else True,
        )

    def _parse_price(self, missing_price_value):
        def found_price(raw_price):
            self.handle_found_price(raw_price, missing_price_value)

        self._try_to_find_and_set_decimal(
            OrderCols.PRICE.value,
            [
                OrderCols.AVERAGE.value,  # first try average as its more accurate
                OrderCols.PRICE.value,
                OrderCols.STOP_PRICE.value,
            ],
            parse_method=found_price,
            not_found_val=missing_price_value,
        )

    def _parse_filled_price(self):
        self._try_to_find_and_set_decimal(
            OrderCols.FILLED_PRICE.value,
            [OrderCols.FILLED_PRICE.value],
            not_found_method=self.missing_filled_price,
            enable_log=False,
        )

    def _parse_amount(self, missing_quantity_value):
        self._try_to_find_and_set_decimal(
            OrderCols.AMOUNT.value,
            [OrderCols.AMOUNT.value],
            missing_quantity_value or 0,
            enable_log=False if missing_quantity_value else True,
        )

    def _parse_cost(self):
        # is this important as its missing sometimes
        # if not self.filled_price and self.filled_quantity:
        #     self.filled_price = self.total_cost / self.filled_quantity
        self._try_to_find_and_set_decimal(OrderCols.COST.value, [OrderCols.COST.value])

    def _parse_average_price(self):
        self._try_to_find_and_set_decimal(
            OrderCols.AVERAGE.value,
            [
                OrderCols.AVERAGE.value,
                OrderCols.PRICE.value,
                OrderCols.STOP_PRICE.value,
            ],
        )

    def _parse_remaining(self):
        self._try_to_find_and_set_decimal(
            OrderCols.REMAINING.value,
            [OrderCols.REMAINING.value],
            not_found_method=self.missing_remaining,
        )

    def _parse_filled_amount(self):
        self._try_to_find_and_set_decimal(
            OrderCols.FILLED.value,
            [OrderCols.FILLED.value],
            not_found_method=self.missing_filled,
        )

    def _parse_taker_or_maker(self):
        self._try_to_find_and_set(
            OrderCols.TAKERORMAKER.value,
            [OrderCols.TAKERORMAKER.value],
            not_found_method=self.missing_taker_or_maker,
        )

    def _parse_reduce_only(self):
        self._try_to_find_and_set(
            OrderCols.REDUCE_ONLY.value,
            [OrderCols.REDUCE_ONLY.value] + ReduceOnlySynonyms.keys,
            not_found_method=self.missing_reduce_only,
            use_info_sub_dict=True,
        )

    def _parse_tag(self):
        # todo find a way
        pass

    def _parse_fees(self):
        self._try_to_find_and_parse_with_method(
            OrderCols.FEE.value,
            [OrderCols.FEE.value],
            parse_method=self.found_fees,
            not_found_method=self.missing_fees,
        )

    async def _fetch_if_missing(self):
        to_find_id = self.formatted_record.get(OrderCols.ID.value)
        if self.debugging_report_dict and to_find_id and \
                (symbol := self.formatted_record.get(OrderCols.SYMBOL.value)):
            if fetched_order := await self.exchange.get_order(
                    order_id=to_find_id, symbol=symbol, check_completeness=False
            ):
                self.fetched_order = fetched_order  # just for debugging purpose
                # overwrite with fetched order details
                for key in (
                        OrderCols.STATUS.value,
                        OrderCols.TIMESTAMP.value,
                        OrderCols.SYMBOL.value,
                        OrderCols.SIDE.value,
                        OrderCols.OCTOBOT_ORDER_TYPE.value,
                        OrderCols.TYPE.value,
                        OrderCols.TAKERORMAKER.value,
                        OrderCols.PRICE.value,
                        OrderCols.FILLED_PRICE.value,
                        OrderCols.AVERAGE.value,
                        OrderCols.AMOUNT.value,
                        OrderCols.REMAINING.value,
                        OrderCols.FILLED.value,
                        OrderCols.COST.value,
                        OrderCols.REDUCE_ONLY.value,
                        OrderCols.TAG.value,
                        OrderCols.FEE.value,
                ):
                    self.set_fetched_attribute(fetched_order, key)

    def set_fetched_attribute(self, fetched_order, key):
        nothing = "nothing"
        value = fetched_order.get(key, nothing)
        if value is nothing:
            return
        self.formatted_record[key] = value
        if key in self.debugging_report_dict:
            self.debugging_report_dict.pop(key)

    # Parse helper methods
    def found_timestamp(self, raw_timestamp):
        # change this before the year 5138
        if (timestamp := int(raw_timestamp)) < 100000000000:
            return timestamp
        return self.exchange.get_uniformized_timestamp(raw_timestamp)

    def parse_exchange_order_type(self, raw_order_type, missing_type_value):
        raw_order_type = raw_order_type.lower()  # just in case
        try:
            exchange_order_type = TradeOrderType(raw_order_type).value
        except ValueError:
            exchange_order_type = convert_type_to_trade_order_type(
                raw_order_type, missing_type_value
            )

        if exchange_order_type:
            self.formatted_record[OrderCols.TYPE.value] = exchange_order_type
            return exchange_order_type
        self._log_missing(
            OrderCols.TYPE.value,
            f"key: {OrderCols.OCTOBOT_ORDER_TYPE.value} got: {raw_order_type or 'no exchange order type'} "
            f"which is not a TradeOrderType or TraderOrderType",
        )

    def handle_type_found(self, raw_order_type, missing_type_value):
        exchange_order_type = self.parse_exchange_order_type(raw_order_type, missing_type_value)
        try:
            # if type is already a TraderOrderType
            return TraderOrderType(raw_order_type).value
        except ValueError:
            if order_type := convert_trade_to_trader_order_type(
                    self, exchange_order_type
            ):
                return order_type

        return self.missing_type(missing_type_value, raw_order_type)

    def missing_type(self, missing_type_value, raw_order_type=None):
        new_type = None
        taker_or_maker = None
        if missing_type_value:
            new_type = missing_type_value
        elif taker_or_maker := self.raw_record.get(OrderCols.TAKERORMAKER.value):
            # todo check - is it safe?
            if self.formatted_record[OrderCols.SIDE.value] == TradeOrderSide.BUY.value:
                if taker_or_maker == MarketCols.TAKER.value:
                    new_type = TraderOrderType.BUY_MARKET.value
                elif taker_or_maker == MarketCols.MAKER.value:
                    new_type = TraderOrderType.BUY_LIMIT.value
            elif self.formatted_record[OrderCols.SIDE.value] == TradeOrderSide.SELL.value:
                if taker_or_maker == MarketCols.TAKER.value:
                    new_type = TraderOrderType.SELL_MARKET.value
                elif taker_or_maker == MarketCols.MAKER.value:
                    new_type = TraderOrderType.SELL_LIMIT.value
        if new_type:
            self.formatted_record[OrderCols.TYPE.value] \
                = self.parse_exchange_order_type(new_type, missing_type_value)
            return new_type
        type_exists_message = (
            f", got: {raw_order_type or 'no exchange order type'} which is not a TradeOrderType or TraderOrderType"
            if raw_order_type
            else ""
        )
        self._log_missing(
            OrderCols.OCTOBOT_ORDER_TYPE.value,
            f"{OrderCols.OCTOBOT_ORDER_TYPE.value} and based on taker_or_maker "
            f"({taker_or_maker or 'no taker_or_maker'}) which also failed to parse{type_exists_message}",
        )

    def handle_found_price(self, raw_price, missing_price_value):
        if (status := self.formatted_record.get(OrderCols.STATUS.value)) \
                and (order_type := self.formatted_record.get(OrderCols.TYPE.value)):
            # todo investigate - ccxt is returning a wrong price (~1000k higher on bybit btc)
            # on open market orders so we dont use it
            # tried with current(1.95.36) and latest (2.1.92) ccxt version
            if missing_price_value and status == OrderStatus.OPEN.value \
                    or status == OrderStatus.PENDING_CREATION.value and order_type == TradeOrderType.MARKET.value:
                return missing_price_value
            return raw_price
        self._log_missing(
            OrderCols.PRICE.value,
            f"Parsing price requires status ({status or 'no status'}) "
            "and order type ({order_type or 'no order type'})",
        )

    def missing_filled_price(self, _):
        # todo check if safe
        filled_quantity = None
        if status := self.formatted_record.get(OrderCols.STATUS.value):
            if (status == OrderStatus.FILLED.value or status == OrderStatus.CLOSED.value) \
                    and (price := self.formatted_record.get(OrderCols.PRICE.value)):
                return price
            if (
                    status == OrderStatus.CANCELED.value
                    or status == OrderStatus.OPEN.value
                    or status == OrderStatus.PENDING_CANCEL.value
                    or status == OrderStatus.EXPIRED.value
                    or status == OrderStatus.PENDING_CREATION.value
                    or status == OrderStatus.REJECTED.value
            ):
                return 0  # to check - should we set it to None?
            if status == OrderStatus.PARTIALLY_FILLED.value:
                pass  # just here so you know whats unhandled
        if (cost := self.formatted_record.get(OrderCols.COST.value)) \
                and (filled_quantity := self.formatted_record.get(OrderCols.FILLED.value)):
            return cost / filled_quantity
        self._log_missing(
            OrderCols.FILLED_PRICE.value,
            f"key: {OrderCols.FILLED_PRICE.value}, "
            f"using status ({status or 'no status'}) and based on "
            f"cost {cost or 'no cost'} / filled quantity ({filled_quantity or 'no filled quantity'})",
        )

    def missing_remaining(self, _):
        if status := self.formatted_record.get(OrderCols.STATUS.value):
            if (
                    status == OrderStatus.FILLED.value
                    or status == OrderStatus.CLOSED.value
                    or status == OrderStatus.CANCELED.value
                    or status == OrderStatus.REJECTED.value
                    or status == OrderStatus.EXPIRED.value
            ):
                return 0
            if (amount := self.formatted_record.get(OrderCols.AMOUNT.value)) and (
                    status == OrderStatus.PENDING_CREATION.value
                    or status == OrderStatus.OPEN.value
                    or status == OrderStatus.PENDING_CANCEL.value
            ):
                return amount
            if status == OrderStatus.PARTIALLY_FILLED.value:
                pass  # just here to let you know whats unhandled

        self._log_missing(
            OrderCols.STATUS.value,
            f"key {OrderCols.REMAINING.value} and based on status ({status or 'no status'})",
        )

    def missing_filled(self, _):
        remaining = None
        if status := self.formatted_record.get(OrderCols.STATUS.value):
            if (amount := self.formatted_record.get(OrderCols.AMOUNT.value)) and (
                    status == OrderStatus.FILLED.value
                    or status == OrderStatus.CLOSED.value
            ):
                return amount
            if (
                    status == OrderStatus.EXPIRED.value
                    or status == OrderStatus.CANCELED.value
                    or status == OrderStatus.REJECTED.value
                    or status == OrderStatus.EXPIRED.value
                    or status == OrderStatus.PENDING_CREATION.value
                    or status == OrderStatus.OPEN.value
                    or status == OrderStatus.PENDING_CANCEL.value
            ):
                return constants.ZERO
            if status == OrderStatus.PARTIALLY_FILLED.value:
                pass  # just here to let you know whats unhandled
        if (amount := self.formatted_record.get(OrderCols.AMOUNT.value)) \
                and (remaining := self.formatted_record.get(OrderCols.REMAINING.value)):
            return amount - remaining

        self._log_missing(
            OrderCols.FILLED.value,
            f"based on {OrderCols.FILLED.value}, "
            f"based on amount ({amount or 'no amount'}) - remaining ({remaining or 'no remaining'})"
            f"based on status ({status.value if status else 'no status'})",
        )

    def missing_taker_or_maker(self, _):
        if order_type := self.formatted_record.get(
                OrderCols.OCTOBOT_ORDER_TYPE.value
        ):
            if order_type in (
                    TraderOrderType.BUY_MARKET.value,
                    TraderOrderType.SELL_MARKET.value,
                    TraderOrderType.STOP_LOSS.value,
                    TraderOrderType.TRAILING_STOP.value,
            ):
                return MarketCols.TAKER.value
            elif order_type in (
                    TraderOrderType.SELL_LIMIT.value,
                    TraderOrderType.BUY_LIMIT.value,
                    TraderOrderType.STOP_LOSS_LIMIT.value,
                    TraderOrderType.TAKE_PROFIT_LIMIT.value,
                    TraderOrderType.TRAILING_STOP_LIMIT.value,
            ):
                return MarketCols.MAKER.value
        self._log_missing(
            OrderCols.TAKERORMAKER.value,
            f"with key {OrderCols.TAKERORMAKER.value} and based on"
            f" order type ({order_type or 'no order_type'})",
        )

    def missing_reduce_only(self, _):
        if self.formatted_record.get(OrderCols.OCTOBOT_ORDER_TYPE.value) == TradeOrderType.STOP_LOSS.value:
            return True
        return None  # dont raise as it's optional

    def missing_fees(self, _):
        # only required for CLOSED and FILLED orders
        if status := self.formatted_record.get(OrderCols.STATUS.value):
            if (
                    status == OrderStatus.CLOSED.value
                    or status == OrderStatus.FILLED.value
            ):
                # fees are missing on bybit trades
                # getting it from the order is also not possible as trade id != order id
                pass
                # self._log_missing(
                #     OrderCols.FEE.value,
                #     f"key: {OrderCols.FEE.value} - fee is required for order_status ({status})",
                # )

    def found_fees(self, fees_dict):
        # fees example for paid fees in USDT:
        # {'code': 'USDT', 'cost': -0.015922}
        if type(fees_dict) is not dict:
            self.missing_fees(None)
        if ExchangeConstantsFeesColumns.CURRENCY.value not in fees_dict and (
                currency := fees_dict.get("code")
        ):
            fees_dict[ExchangeConstantsFeesColumns.CURRENCY.value] = currency
        if fee := fees_dict[ExchangeConstantsFeesColumns.COST.value]:
            fees_dict[ExchangeConstantsFeesColumns.COST.value] = (
                fee * -1 if fee < 0 else fee
            )
        if (
                fees_dict[ExchangeConstantsFeesColumns.CURRENCY.value]
                and fees_dict[ExchangeConstantsFeesColumns.COST.value]
        ):
            return
        self.missing_fees(None)


def found_side(raw_side):
    return TradeOrderSide(raw_side).value


def try_cryptofeed_order_status(raw_order_status):
    if raw_order_status == cryptofeed_constants.OPEN:
        return OrderStatus.OPEN.value
    elif raw_order_status == cryptofeed_constants.PENDING:
        return OrderStatus.OPEN.value
    elif raw_order_status == cryptofeed_constants.FILLED:
        return OrderStatus.FILLED.value
    elif raw_order_status == cryptofeed_constants.PARTIAL:
        return OrderStatus.PARTIALLY_FILLED.value
    elif raw_order_status == cryptofeed_constants.CANCELLED:
        return OrderStatus.CANCELED.value
    elif raw_order_status == cryptofeed_constants.UNFILLED:
        return OrderStatus.OPEN.value
    elif raw_order_status == cryptofeed_constants.EXPIRED:
        return OrderStatus.EXPIRED.value
    elif raw_order_status == cryptofeed_constants.FAILED:
        return OrderStatus.REJECTED.value
    elif raw_order_status == cryptofeed_constants.SUBMITTING:
        return OrderStatus.PENDING_CREATION.value
    elif raw_order_status == cryptofeed_constants.CANCELLING:
        return OrderStatus.PENDING_CANCEL.value
    elif raw_order_status == cryptofeed_constants.CLOSED:
        return OrderStatus.CLOSED.value
    elif raw_order_status == cryptofeed_constants.SUSPENDED:
        pass  # todo is it canceled?


def convert_trade_to_trader_order_type(parser, exchange_order_type):
    if exchange_order_type:
        if parser.formatted_record[OrderCols.SIDE.value] == TradeOrderSide.BUY.value:
            if (
                    exchange_order_type == TradeOrderType.LIMIT.value
                    or exchange_order_type == TradeOrderType.LIMIT_MAKER.value
            ):
                return TraderOrderType.BUY_LIMIT.value
            if exchange_order_type == TradeOrderType.MARKET.value:
                return TraderOrderType.BUY_MARKET.value
        if parser.formatted_record[OrderCols.SIDE.value] == TradeOrderSide.SELL.value:
            if (
                    exchange_order_type == TradeOrderType.LIMIT.value
                    or exchange_order_type == TradeOrderType.LIMIT_MAKER.value
            ):
                return TraderOrderType.SELL_LIMIT.value
            if exchange_order_type == TradeOrderType.MARKET.value:
                return TraderOrderType.SELL_MARKET.value


def convert_type_to_trade_order_type(
        raw_order_type: str, missing_type_value: str
) -> typing.Union[TradeOrderType, None]:
    # try cryptofeed_constants
    if raw_order_type == cryptofeed_constants.LIMIT:
        return TradeOrderType.LIMIT.value
    if raw_order_type == cryptofeed_constants.MARKET:
        return TradeOrderType.MARKET.value
    if raw_order_type == cryptofeed_constants.STOP_LIMIT:
        return TradeOrderType.STOP_LOSS_LIMIT.value
    if raw_order_type == cryptofeed_constants.STOP_MARKET:
        return TradeOrderType.STOP_LOSS.value
    # if raw_order_type == cryptofeed_constants.MAKER_OR_CANCEL:
    #     pass
    # if raw_order_type == cryptofeed_constants.FILL_OR_KILL:
    #     pass
    # if raw_order_type == cryptofeed_constants.IMMEDIATE_OR_CANCEL:
    #     pass
    # if raw_order_type == cryptofeed_constants.GOOD_TIL_CANCELED:
    #     pass

    # convert from TraderOrderType
    try:
        trader_order_type = TraderOrderType(raw_order_type)
    except ValueError:
        if missing_type_value:
            trader_order_type = TraderOrderType(missing_type_value)
        return None
    if (
            trader_order_type is TraderOrderType.BUY_LIMIT
            or trader_order_type is TraderOrderType.SELL_LIMIT
    ):
        return TradeOrderType.LIMIT.value
    if (
            trader_order_type is TraderOrderType.BUY_MARKET
            or trader_order_type is TraderOrderType.SELL_MARKET
    ):
        return TradeOrderType.MARKET.value
    if trader_order_type is TraderOrderType.STOP_LOSS:
        return TradeOrderType.STOP_LOSS.value
    if trader_order_type is TraderOrderType.TAKE_PROFIT_LIMIT:
        return TradeOrderType.TAKE_PROFIT_LIMIT.value
    if trader_order_type is TraderOrderType.STOP_LOSS_LIMIT:
        return TradeOrderType.STOP_LOSS_LIMIT.value
    if trader_order_type is TraderOrderType.TRAILING_STOP_LIMIT:
        return TradeOrderType.TRAILING_STOP_LIMIT.value
    if trader_order_type is TraderOrderType.TRAILING_STOP:
        return TradeOrderType.TRAILING_STOP.value
    if trader_order_type is TraderOrderType.TAKE_PROFIT:
        return TradeOrderType.TAKE_PROFIT.value

    return None


class ReduceOnlySynonyms:
    keys = ["reduce_only"]
