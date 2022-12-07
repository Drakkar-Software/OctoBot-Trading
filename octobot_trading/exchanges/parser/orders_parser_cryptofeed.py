import cryptofeed.defines as cryptofeed_constants
from octobot_trading.enums import (
    OrderStatus,
    TradeOrderSide,
    TraderOrderType,
)
import cryptofeed.types as cryptofeed_types
import octobot_trading.exchanges.parser.orders_parser as orders_parser


class CryptoFeedOrdersParser(orders_parser.OrdersParser):
    """
    override CryptoFeedOrdersParser if you add support for a crypto feed exchange

    parser usage:   parser = CryptoFeedOrdersParser(exchange)
                    orders = await parser.parse_orders(raw_orders)
                    order = await parser.parse_order(raw_order)
    """
    TIMESTAMP_KEYS: list = ["timestamp"]
    STATUS_KEYS: list = ["status"]
    ID_KEYS: list = ["id"]
    SYMBOL_KEYS: list = ["symbol"]
    SIDE_KEYS: list = ["side"]
    TYPE_KEYS: list = ["type"]
    TAKER_OR_MAKER_KEYS: list = []
    PRICE_KEYS: list = ["price"]
    FILLED_PRICE_KEYS: list = []
    AVERAGE_PRICE_KEYS: list = []
    AMOUNT_KEYS: list = ["amount"]
    REMAINING_KEYS: list = ["remaining"]
    FILLED_AMOUNT_KEYS: list = []
    COST_KEYS: list = []
    REDUCE_ONLY_KEYS: list = []
    POST_ONLY_KEYS: list = []
    TAG_KEYS: list = []
    FEE_KEYS: list = []
    QUANTITY_CURRENCY_KEYS: list = []
    
    def __init__(self, exchange):
        super().__init__(exchange=exchange)
        self.PARSER_TITLE = "crypto feed orders"

    STATUS_MAP: dict = {
        # for example:
        # "weirdClosedStatus": OrderStatus.CLOSED.value,
        # "weirdSecondClosedStatus": OrderStatus.CLOSED.value,
        cryptofeed_constants.OPEN: OrderStatus.OPEN.value,
        cryptofeed_constants.PENDING: OrderStatus.OPEN.value,
        cryptofeed_constants.FILLED: OrderStatus.FILLED.value,
        cryptofeed_constants.PARTIAL: OrderStatus.PARTIALLY_FILLED.value,
        cryptofeed_constants.CANCELLED: OrderStatus.CANCELED.value,
        cryptofeed_constants.UNFILLED: OrderStatus.OPEN.value,
        cryptofeed_constants.EXPIRED: OrderStatus.EXPIRED.value,
        cryptofeed_constants.FAILED: OrderStatus.REJECTED.value,
        cryptofeed_constants.SUBMITTING: OrderStatus.PENDING_CREATION.value,
        cryptofeed_constants.CANCELLING: OrderStatus.PENDING_CANCEL.value,
        cryptofeed_constants.CLOSED: OrderStatus.CLOSED.value,
        # cryptofeed_constants.SUSPENDED:  # todo is it canceled?
    }

    TRADER_ORDER_TYPE_MAP: dict = {
        # for example:
        # "weirdStopOrder": TraderOrderType.STOP_LOSS.value,
        # "weirdSecondStop": TraderOrderType.STOP_LOSS.value,
        cryptofeed_constants.LIMIT: TraderOrderType.SELL_LIMIT.value,
        cryptofeed_constants.MARKET: TraderOrderType.SELL_MARKET.value,
        cryptofeed_constants.STOP_LIMIT: TraderOrderType.STOP_LOSS_LIMIT.value,
        cryptofeed_constants.STOP_MARKET: TraderOrderType.STOP_LOSS.value,
        cryptofeed_constants.MAKER_OR_CANCEL: TraderOrderType.SELL_LIMIT.value,
        # cryptofeed_constants.FILL_OR_KILL: ,
        # cryptofeed_constants.IMMEDIATE_OR_CANCEL: ,
        # cryptofeed_constants.GOOD_TIL_CANCELED: ,
        # cryptofeed_constants.TRIGGER_LIMIT: ,
        # cryptofeed_constants.TRIGGER_MARKET: ,
        # cryptofeed_constants.MARGIN_LIMIT: ,
        # cryptofeed_constants.MARGIN_MARKET: ,
    }
    TRADER_ORDER_TYPE_BUY_MAP: dict = {
        # for example:
        # "weirdLimitOrder": TraderOrderType.BUY_LIMIT.value,
        # "weirdSecondLimit": TraderOrderType.BUY_LIMIT.value,
        cryptofeed_constants.LIMIT: TraderOrderType.BUY_LIMIT.value,
        cryptofeed_constants.MARKET: TraderOrderType.BUY_MARKET.value,
        cryptofeed_constants.MAKER_OR_CANCEL: TraderOrderType.BUY_LIMIT.value,
    }
    TRADER_ORDER_TYPE_SELL_MAP: dict = {
        # for example:
        # "weirdLimitOrder": TraderOrderType.SELL_LIMIT.value,
        # "weirdSecondLimit": TraderOrderType.SELL_LIMIT.value,
        cryptofeed_constants.LIMIT: TraderOrderType.SELL_LIMIT.value,
        cryptofeed_constants.MARKET: TraderOrderType.SELL_MARKET.value,
        cryptofeed_constants.MAKER_OR_CANCEL: TraderOrderType.SELL_LIMIT.value,
    }

    TRADE_ORDER_SIDE_MAP: dict = {
        TradeOrderSide.BUY.value: TradeOrderSide.BUY.value,
        TradeOrderSide.SELL.value: TradeOrderSide.SELL.value,
    }

    async def parse_orders(self):
        raise NotImplementedError

    async def parse_order(
        self,
        crypto_feed_order: cryptofeed_types.OrderInfo,
        check_completeness: bool = True,
    ) -> dict:
        """
        use this method to format a single order

        :param crypto_feed_order: crypto_feed_order with eventually missing data

        :param check_completeness: if true checks all attributes,
            if somethings missing it'll try to fetch it from the exchange

        :return: formatted order dict (100% complete or we raise NotImplemented)

        """

        await super().parse_order(
            raw_order=crypto_feed_order.__dict__, check_completeness=check_completeness
        )
