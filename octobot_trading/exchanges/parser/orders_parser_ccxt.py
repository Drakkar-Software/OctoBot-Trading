from octobot_trading.enums import (
    ExchangeOrderCCXTColumns as CCXTOrderCols,
    ExchangeConstantsOrderColumns as OrderCols,
    OrderStatus,
    TraderOrderType,
    TradeOrderType,
)
import octobot_trading.exchanges.parser.orders_parser as orders_parser


class CCXTOrdersParser(orders_parser.OrdersParser):
    """
    override CCXTOrdersParser if you add support for a CCXT exchange
    dont use GenericCCXTOrdersParser as a base

    parser usage:   parser = CCXTOrdersParser(exchange)
                    orders = await parser.parse_orders(raw_orders)
                    order = await parser.parse_order(raw_order)
    """

    TIMESTAMP_KEYS: list = [CCXTOrderCols.TIMESTAMP.value]
    STATUS_KEYS: list = [CCXTOrderCols.STATUS.value]
    ID_KEYS: list = [CCXTOrderCols.ID.value]
    SYMBOL_KEYS: list = [CCXTOrderCols.SYMBOL.value]
    SIDE_KEYS: list = [CCXTOrderCols.SIDE.value]
    TYPE_KEYS: list = [CCXTOrderCols.TYPE.value]
    TAKER_OR_MAKER_KEYS: list = [CCXTOrderCols.TAKER_OR_MAKER.value]
    PRICE_KEYS: list = [
        CCXTOrderCols.AVERAGE.value,  # first try average as its more accurate
        CCXTOrderCols.PRICE.value,
        CCXTOrderCols.STOP_PRICE.value,  # use only if others are missing
    ]
    FILLED_PRICE_KEYS: list = []  # todo
    AVERAGE_PRICE_KEYS: list = [
        CCXTOrderCols.AVERAGE.value,
        CCXTOrderCols.PRICE.value,
        CCXTOrderCols.STOP_PRICE.value,
    ]
    AMOUNT_KEYS: list = [CCXTOrderCols.AMOUNT.value]
    REMAINING_KEYS: list = [CCXTOrderCols.REMAINING.value]
    FILLED_AMOUNT_KEYS: list = []  # todo
    COST_KEYS: list = [CCXTOrderCols.COST.value]
    REDUCE_ONLY_KEYS: list = [CCXTOrderCols.REDUCE_ONLY.value]
    POST_ONLY_KEYS: list = []
    TAG_KEYS: list = [CCXTOrderCols.TAG.value]
    FEE_KEYS: list = [CCXTOrderCols.FEE, CCXTOrderCols.FEES.value]
    QUANTITY_CURRENCY_KEYS: list = [CCXTOrderCols.QUANTITY_CURRENCY.value]

    def __init__(self, exchange):
        super().__init__(exchange=exchange)
        self.PARSER_TITLE = "ccxt orders"

    def _parse_octobot_order_type(self, missing_type_value=None):
        super()._parse_octobot_order_type(missing_type_value)
        # market orders with no price but with stop price are stop orders
        if self.raw_record.get(OrderCols.STOP_PRICE.value) and not self.raw_record.get(
            OrderCols.PRICE.value
        ):
            if (
                (_type := self.formatted_record[OrderCols.OCTOBOT_ORDER_TYPE.value])
                == TraderOrderType.SELL_MARKET.value
                or _type == TraderOrderType.BUY_MARKET.value
            ):
                self.formatted_record[
                    OrderCols.OCTOBOT_ORDER_TYPE.value
                ] = TraderOrderType.STOP_LOSS.value
