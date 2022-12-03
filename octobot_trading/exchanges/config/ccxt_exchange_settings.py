import octobot_trading.enums as enums
import octobot_trading.exchanges.parser as parser


class CCXTExchangeConfig:
    """
    override this class if you need custom settings
    """

    def __init__(self, exchange_connector):

        # available methods to choose from
        self.ALL_GET_ORDER_METHODS = [
            exchange_connector.get_order_default.__name__,
            exchange_connector.get_order_from_open_and_closed_orders.__name__,
            exchange_connector.get_order_from_open_and_closed_orders.__name__,
            exchange_connector.get_trade.__name__,
        ]
        self.ALL_GET_ALL_ORDERS_METHODS = [
            exchange_connector.get_all_orders_default.__name__,
            exchange_connector.get_all_stop_orders_using_stop_loss_endpoint.__name__,
        ]
        self.ALL_GET_OPEN_ORDERS_METHODS = [
            exchange_connector.get_open_orders_default.__name__,
            exchange_connector.get_open_stop_orders_using_stop_loss_endpoint.__name__,
        ]
        self.ALL_GET_CLOSED_ORDERS_METHODS = [
            exchange_connector.get_closed_orders_default.__name__,
            exchange_connector.get_closed_stop_orders_using_stop_loss_endpoint.__name__,
        ]
        self.ALL_CANCEL_ORDERS_METHODS = [
            exchange_connector.cancel_order_default.__name__,
            exchange_connector.cancel_stop_order_using_stop_loss_endpoint.__name__,
        ]
        self.ALL_GET_MY_RECENT_TRADES_METHODS = [
            exchange_connector.get_my_recent_trades_default.__name__,
            exchange_connector.get_my_recent_trades_using_recent_trades.__name__,
            exchange_connector.get_my_recent_trades_using_closed_orders.__name__,
        ]
        self.ALL_GET_POSITION_METHODS = [
            exchange_connector.get_position_default.__name__,
            exchange_connector.get_position_by_sub_type.__name__,
            exchange_connector.get_position_with_private_get_position_risk.__name__,
        ]
        self.GET_ORDER_METHODS = self.ALL_GET_ORDER_METHODS
        self.GET_ALL_ORDERS_METHODS = self.ALL_GET_ALL_ORDERS_METHODS
        self.GET_OPEN_ORDERS_METHODS = self.ALL_GET_OPEN_ORDERS_METHODS
        self.GET_CLOSED_ORDERS_METHODS = self.ALL_GET_CLOSED_ORDERS_METHODS
        self.CANCEL_ORDERS_METHODS = self.ALL_CANCEL_ORDERS_METHODS
        self.GET_MY_RECENT_TRADES_METHODS = self.ALL_GET_MY_RECENT_TRADES_METHODS
        self.GET_POSITION_METHODS = self.ALL_GET_POSITION_METHODS

    # set this for each exchange if tested on testnet and real money

    IS_FULLY_TESTED_AND_SUPPORTED = False  # not recommended

    CANDLE_LOADING_LIMIT_IS_FULLY_TESTED_AND_SUPPORTED = False
    MAX_RECENT_TRADES_PAGINATION_LIMIT_IS_FULLY_TESTED_AND_SUPPORTED = False
    MAX_ORDER_PAGINATION_LIMIT_IS_FULLY_TESTED_AND_SUPPORTED = False
    MARKET_STATUS_IS_FULLY_TESTED_AND_SUPPORTED = False
    GET_ORDER_METHODS_IS_FULLY_TESTED_AND_SUPPORTED = False
    GET_ALL_ORDERS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED = False
    GET_OPEN_ORDERS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED = False
    GET_CLOSED_ORDERS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED = False
    CANCEL_ORDERS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED = False
    GET_MY_RECENT_TRADES_METHODS_IS_FULLY_TESTED_AND_SUPPORTED = False
    GET_POSITION_METHODS_IS_FULLY_TESTED_AND_SUPPORTED = False

    @classmethod
    def is_fully_tested_and_supported(cls):
        return cls.IS_FULLY_TESTED_AND_SUPPORTED or (
            cls.CANDLE_LOADING_LIMIT_IS_FULLY_TESTED_AND_SUPPORTED
            and cls.MAX_RECENT_TRADES_PAGINATION_LIMIT_IS_FULLY_TESTED_AND_SUPPORTED
            and cls.MAX_ORDER_PAGINATION_LIMIT_IS_FULLY_TESTED_AND_SUPPORTED
            and cls.MARKET_STATUS_IS_FULLY_TESTED_AND_SUPPORTED
            and cls.GET_ORDER_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
            and cls.GET_ALL_ORDERS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
            and cls.GET_OPEN_ORDERS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
            and cls.GET_CLOSED_ORDERS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
            and cls.CANCEL_ORDERS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
            and cls.GET_MY_RECENT_TRADES_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
            and cls.GET_POSITION_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
        )

    # set default exchange config here

    # override classes if you need a different parser
    ORDERS_PARSER_CLASS = parser.OrdersParser
    TRADES_PARSER_CLASS = parser.TradesParser
    POSITIONS_PARSER_CLASS = parser.PositionsParser
    TICKER_PARSER_CLASS = parser.TickerParser
    MARKET_STATUS_PARSER_CLASS = parser.ExchangeMarketStatusParser

    MARKET_STATUS_FIX_PRECISION = False
    MARKET_STATUS_REMOVE_INVALID_PRICE_LIMITS = False

    FUNDING_IN_TICKER = True
    MARK_PRICE_IN_TICKER = True
    FUNDING_WITH_MARK_PRICE = True
    MARK_PRICE_IN_POSITION = True

    CANDLE_LOADING_LIMIT = 0
    MAX_RECENT_TRADES_PAGINATION_LIMIT = 0
    MAX_ORDER_PAGINATION_LIMIT = 0

    ADD_COST_TO_CREATE_SPOT_MARKET_ORDER = False
    ADD_COST_TO_CREATE_FUTURE_MARKET_ORDER = False
