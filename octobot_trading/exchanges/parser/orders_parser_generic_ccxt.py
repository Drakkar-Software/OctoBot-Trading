import octobot_trading.constants as constants
from octobot_trading.enums import (
    ExchangeConstantsOrderColumns as OrderCols,
    ExchangeOrderCCXTColumns as CCXTOrderCols,
    OrderStatus,
    TradeOrderSide,
)
from octobot_trading.enums import TradeOrderType as TradeOrderType
import octobot_trading.exchanges.parser.orders_parser_ccxt as orders_parser_ccxt
from octobot_trading.exchanges.parser.orders_parser_cryptofeed import (
    CryptoFeedOrdersParser,
)


class GenericCCXTOrdersParser(orders_parser_ccxt.CCXTOrdersParser):
    """
    Dont override this class, use CCXTOrdersParser instead

    always/only include bulletproof custom code into the parser to improve generic support

    parser usage:   parser = GenericCCXTOrdersParser(exchange)
                    orders = await parser.parse_orders(raw_orders)
                    order = await parser.parse_order(raw_order)
    """

    TEST_AND_FIX_SPOT_QUANTITIES: bool = False
    TEST_AND_FIX_FUTURES_QUANTITIES: bool = False

    REDUCE_ONLY_KEYS: list = [CCXTOrderCols.REDUCE_ONLY.value, "reduce_only"]
    USE_INFO_SUB_DICT_FOR_REDUCE_ONLY: bool = True

    FILLED_PRICE_KEYS: list = [OrderCols.FILLED_PRICE.value]
    FILLED_AMOUNT_KEYS: list = [OrderCols.FILLED_AMOUNT.value]

    STATUS_MAP: dict = {
        # for example:
        # "weirdClosedStatus": OrderStatus.CLOSED.value,
        # "weirdSecondClosedStatus": OrderStatus.CLOSED.value,
        **orders_parser_ccxt.CCXTOrdersParser.STATUS_MAP,
        "ORDER_NEW": OrderStatus.OPEN.value,
        "PARTIALLY_FILLED_CANCELED": OrderStatus.PARTIALLY_FILLED.value,
        "ORDER_FILLED": OrderStatus.FILLED.value,
        "ORDER_CANCELED": OrderStatus.CANCELED.value,
        "cancelled": OrderStatus.CANCELED.value,
        **CryptoFeedOrdersParser.STATUS_MAP,
    }

    TRADER_ORDER_TYPE_MAP: dict = {
        # for example:
        # "weirdStopOrder": TraderOrderType.STOP_LOSS.value,
        # "weirdSecondStop": TraderOrderType.STOP_LOSS.value,
        # TraderOrderTypes
        **orders_parser_ccxt.CCXTOrdersParser.TRADER_ORDER_TYPE_MAP,
        **CryptoFeedOrdersParser.TRADER_ORDER_TYPE_MAP,
    }
    TRADER_ORDER_TYPE_BUY_MAP: dict = {
        # for example:
        # "weirdLimitOrder": TraderOrderType.BUY_LIMIT.value,
        # "weirdSecondLimit": TraderOrderType.BUY_LIMIT.value,
        **orders_parser_ccxt.CCXTOrdersParser.TRADER_ORDER_TYPE_BUY_MAP,
        **CryptoFeedOrdersParser.TRADER_ORDER_TYPE_BUY_MAP,
    }
    TRADER_ORDER_TYPE_SELL_MAP: dict = {
        # for example:
        # "weirdLimitOrder": TraderOrderType.SELL_LIMIT.value,
        # "weirdSecondLimit": TraderOrderType.SELL_LIMIT.value,
        **orders_parser_ccxt.CCXTOrdersParser.TRADER_ORDER_TYPE_SELL_MAP,
        **CryptoFeedOrdersParser.TRADER_ORDER_TYPE_SELL_MAP,
    }

    def __init__(self, exchange):
        super().__init__(exchange=exchange)
        self.PARSER_TITLE = "generic ccxt orders"

    def _parse_id(self):
        self._try_to_find_and_set(
            OrderCols.ID.value,
            self.ID_KEYS,
            not_found_method=self.missing_id,
        )

    def missing_id(self, _):
        # some exchanges dont provide an id
        # use time instead on orders where its not critical
        if (
                (status := self.formatted_record.get(OrderCols.STATUS.value))
                == OrderStatus.CLOSED.value
                or status == OrderStatus.CANCELED.value
                or status == OrderStatus.EXPIRED.value
                or status == OrderStatus.REJECTED.value
        ):
            return self.formatted_record.get(OrderCols.TIMESTAMP.value)
        else:
            self._log_missing(OrderCols.ID.value, f"{self.ID_KEYS}")

    def _parse_side(self, missing_side_value):
        self._try_to_find_and_set(
            OrderCols.SIDE.value,
            self.SIDE_KEYS,
            parse_method=self._found_side,
            not_found_val=missing_side_value,
            not_found_method=self.missing_side,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_SIDE,
        )

    def missing_side(self, missing_side_value):
        if missing_side_value:
            return missing_side_value
        if buyer_maker := (
                self.raw_record[CCXTOrderCols.INFO.value].get("isBuyerMaker")
        ):
            return TradeOrderSide.BUY.value
        elif buyer_maker is False:
            return TradeOrderSide.SELL.value
        else:
            self._log_missing(OrderCols.SIDE.value, f"{self.SIDE_KEYS}")

    def _parse_price(self, missing_price_value):
        def handle_found_price(raw_price):
            return self.found_price(raw_price, missing_price_value)

        self._try_to_find_and_set_decimal(
            OrderCols.PRICE.value,
            self.PRICE_KEYS,
            parse_method=handle_found_price,
            not_found_val=missing_price_value,
        )

    def found_price(self, raw_price, missing_price_value):
        order_type = None
        if (status := self.formatted_record.get(OrderCols.STATUS.value)) and (
                order_type := self.formatted_record.get(OrderCols.TYPE.value)
        ):
            # todo investigate - ccxt is returning a wrong price (~1000k higher on bybit btc)
            # on open market orders so we dont use it
            # tried with ccxt 1.95.36 and 2.1.92
            if (
                    missing_price_value
                    and (
                    status == OrderStatus.OPEN.value
                    or status == OrderStatus.PENDING_CREATION.value
            )
                    and order_type == TradeOrderType.MARKET.value
            ):
                return missing_price_value
            return raw_price
        self._log_missing(
            OrderCols.PRICE.value,
            f"Parsing price requires status ({status or 'no status'}) "
            f"and order type ({order_type or 'no order type'})",
        )

    def _parse_filled_price(self):
        self._try_to_find_and_set_decimal(
            OrderCols.FILLED_PRICE.value,
            self.FILLED_PRICE_KEYS,
            not_found_method=self.missing_filled_price,
            enable_log=False,
        )

    def missing_filled_price(self, _):
        # todo check if safe
        filled_quantity = None
        if status := self.formatted_record.get(OrderCols.STATUS.value):
            if (
                    status == OrderStatus.FILLED.value
                    or status == OrderStatus.CLOSED.value
                    or status == OrderStatus.PARTIALLY_FILLED.value
            ) and (price := self.formatted_record.get(OrderCols.PRICE.value)):
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
        if (cost := self.formatted_record.get(OrderCols.COST.value)) and (
                filled_quantity := self.formatted_record.get(OrderCols.FILLED_AMOUNT.value)
        ):
            return cost / filled_quantity
        self._log_missing(
            OrderCols.FILLED_PRICE.value,
            f"key: {self.FILLED_PRICE_KEYS}, "
            f"using status ({status or 'no status'}) and based on "
            f"cost {cost or 'no cost'} / filled quantity ({filled_quantity or 'no filled quantity'})",
        )

    def _parse_amount(self, missing_quantity_value):
        def handle_amount_found(amount):
            return self._amount_found(amount, missing_quantity_value)

        self._try_to_find_and_set_decimal(
            OrderCols.AMOUNT.value,
            self.AMOUNT_KEYS,
            parse_method=handle_amount_found,
            not_found_val=missing_quantity_value,
            enable_log=False if missing_quantity_value else True,
        )

    def _amount_found(self, amount, missing_quantity_value):
        if (
                missing_quantity_value
                and self.formatted_record.get(OrderCols.STATUS.value)
                == OrderStatus.OPEN.value
                and self.formatted_record.get(OrderCols.TYPE.value)
                == TradeOrderType.MARKET.value
        ):
            # on open market orders dont use values from the response as they are often wrong
            return missing_quantity_value
        return amount

    def _parse_remaining(self, ):
        if (self.formatted_record.get(OrderCols.STATUS.value)
                == OrderStatus.OPEN.value
                and self.formatted_record.get(OrderCols.TYPE.value)
                == TradeOrderType.MARKET.value
        ):
            # dont use fetched value on open market orders
            self.formatted_record[OrderCols.REMAINING.value] = self.formatted_record.get(OrderCols.AMOUNT)
        else:
            super()._parse_remaining()

    async def _apply_after_parse_fixes(self):
        if (
                self.exchange.exchange_manager.is_spot_only
                and self.TEST_AND_FIX_SPOT_QUANTITIES
        ) or (
                self.exchange.exchange_manager.is_future
                and self.TEST_AND_FIX_FUTURES_QUANTITIES
        ):
            amount = self.formatted_record.get(OrderCols.AMOUNT.value)
            cost = self.formatted_record.get(OrderCols.COST.value)
            filled = self.formatted_record.get(OrderCols.FILLED_AMOUNT.value)
            remaining = self.formatted_record.get(OrderCols.REMAINING.value)
            status = self.formatted_record.get(OrderCols.STATUS.value)
            price = self.formatted_record.get(OrderCols.PRICE.value)
            # fix amount
            if (
                    status == OrderStatus.CLOSED.value
                    or status == OrderStatus.FILLED.value
                    or status == OrderStatus.CANCELED.value
            ):
                if price and amount and cost:
                    if amount * price != cost:
                        # amount mismatch - calculate based on cost
                        amount = self.formatted_record[OrderCols.AMOUNT.value] = (
                                cost / price
                        )
                elif status != OrderStatus.CANCELED.value:
                    self._log_missing(
                        OrderCols.AMOUNT.value,
                        f"price ({price or 'no price'}),"
                        f" amount ({amount or 'no amount'}) and "
                        f"cost ({cost or 'no cost'}) is required to test and fix quantities",
                    )

            # fix filled and remaining and cost
            if (
                    status == OrderStatus.OPEN.value
                    or status == OrderStatus.PENDING_CREATION.value
            ):
                if filled != constants.ZERO:
                    self.formatted_record[OrderCols.FILLED_AMOUNT.value] = constants.ZERO
                if cost != constants.ZERO:
                    self.formatted_record[OrderCols.COST.value] = constants.ZERO
                if remaining != amount:
                    self.formatted_record[OrderCols.REMAINING.value] = amount

            elif (
                    status == OrderStatus.CLOSED.value or status == OrderStatus.FILLED.value
            ):
                if filled != amount:
                    self.formatted_record[OrderCols.FILLED_AMOUNT.value] = amount
                if remaining != constants.ZERO:
                    self.formatted_record[OrderCols.REMAINING.value] = constants.ZERO

            elif (
                    status == OrderStatus.CANCELED.value
                    or status == OrderStatus.EXPIRED.value
                    or status == OrderStatus.REJECTED.value
            ):
                if filled != amount:
                    self.formatted_record[OrderCols.FILLED_AMOUNT.value] = amount
                if remaining != constants.ZERO:
                    self.formatted_record[OrderCols.REMAINING.value] = constants.ZERO
                if cost != constants.ZERO:
                    self.formatted_record[OrderCols.COST.value] = constants.ZERO
            elif status == OrderStatus.PARTIALLY_FILLED.value:
                if filled == amount:
                    self.formatted_record[OrderCols.REMAINING.value] = constants.ZERO
                    self.formatted_record[
                        OrderCols.STATUS.value
                    ] = OrderStatus.CLOSED.value
