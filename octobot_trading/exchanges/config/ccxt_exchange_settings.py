import octobot_trading.exchanges.parser as parser


class CCXTExchangeConfig:
    """
    override this class if you need custom settings
    """

    # override classes if you need a different parser
    MARKET_STATUS_PARSER: parser.ExchangeMarketStatusParser = parser.ExchangeMarketStatusParser
    ORDERS_PARSER: parser.OrdersParser = parser.OrdersParser
    TRADES_PARSER: parser.TradesParser = parser.TradesParser
    POSITIONS_PARSER: parser.PositionsParser = parser.PositionsParser
    TICKER_PARSER: parser.TickerParser = parser.TickerParser

    def __init__(self, exchange_connector):
        self.set_all_get_methods(exchange_connector)
        self.set_default_settings(exchange_connector)
        self.set_connector_settings(exchange_connector)

    def set_connector_settings(self, exchange_connector) -> None:
        """
        override this method to change default settings
        for example:
            self.MARKET_STATUS_PARSER.FIX_PRECISION = True
            self.MARK_PRICE_IN_POSITION = True
        """
        pass

    # set test status for each exchange if tested on testnet and real money

    IS_FULLY_TESTED_AND_SUPPORTED = False  # not recommended

    CANDLE_LOADING_LIMIT_IS_FULLY_TESTED_AND_SUPPORTED = False
    MAX_RECENT_TRADES_PAGINATION_LIMIT_IS_FULLY_TESTED_AND_SUPPORTED = False
    MAX_ORDER_PAGINATION_LIMIT_IS_FULLY_TESTED_AND_SUPPORTED = False

    MARKET_STATUS_IS_FULLY_TESTED_AND_SUPPORTED = False
    ORDERS_PARSER_IS_FULLY_TESTED_AND_SUPPORTED = False
    TRADES_PARSER_IS_FULLY_TESTED_AND_SUPPORTED = False
    POSITIONS_PARSER_IS_FULLY_TESTED_AND_SUPPORTED = False
    TICKER_PARSER_IS_FULLY_TESTED_AND_SUPPORTED = False

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
                and cls.ORDERS_PARSER_IS_FULLY_TESTED_AND_SUPPORTED
                and cls.TRADES_PARSER_IS_FULLY_TESTED_AND_SUPPORTED
                and cls.POSITIONS_PARSER_IS_FULLY_TESTED_AND_SUPPORTED
                and cls.TICKER_PARSER_IS_FULLY_TESTED_AND_SUPPORTED
                and cls.GET_ORDER_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
                and cls.GET_ALL_ORDERS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
                and cls.GET_OPEN_ORDERS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
                and cls.GET_CLOSED_ORDERS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
                and cls.CANCEL_ORDERS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
                and cls.GET_MY_RECENT_TRADES_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
                and cls.GET_POSITION_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
        )

    def set_default_settings(self, exchange_connector):
        # pagination limits
        self.CANDLE_LOADING_LIMIT = 0
        self.MAX_RECENT_TRADES_PAGINATION_LIMIT = 0
        self.MAX_ORDER_PAGINATION_LIMIT = 0

        # define available get methods
        self.GET_ORDER_METHODS = self.ALL_GET_ORDER_METHODS
        self.GET_ALL_ORDERS_METHODS = self.ALL_GET_ALL_ORDERS_METHODS
        self.GET_OPEN_ORDERS_METHODS = self.ALL_GET_OPEN_ORDERS_METHODS
        self.GET_CLOSED_ORDERS_METHODS = self.ALL_GET_CLOSED_ORDERS_METHODS
        self.CANCEL_ORDERS_METHODS = self.ALL_CANCEL_ORDERS_METHODS
        self.GET_MY_RECENT_TRADES_METHODS = self.ALL_GET_MY_RECENT_TRADES_METHODS
        self.GET_POSITION_METHODS = self.ALL_GET_POSITION_METHODS
        self.GET_SYMBOL_POSITION_METHODS = self.ALL_GET_SYMBOL_POSITION_METHODS

        # market status parser
        self.MARKET_STATUS_PARSER.FIX_PRECISION = self.MARKET_STATUS_PARSER.FIX_PRECISION
        self.MARKET_STATUS_PARSER.REMOVE_INVALID_PRICE_LIMITS = self.MARKET_STATUS_PARSER.REMOVE_INVALID_PRICE_LIMITS
        self.MARKET_STATUS_PARSER.LIMIT_PRICE_MULTIPLIER = self.MARKET_STATUS_PARSER.LIMIT_PRICE_MULTIPLIER
        self.MARKET_STATUS_PARSER.LIMIT_COST_MULTIPLIER = self.MARKET_STATUS_PARSER.LIMIT_COST_MULTIPLIER
        self.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MAX_SUP_ATTENUATION = (
            self.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MAX_SUP_ATTENUATION
        )
        self.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MAX_MINUS_3_ATTENUATION = (
            self.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MAX_MINUS_3_ATTENUATION
        )
        self.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MIN_ATTENUATION = self.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MIN_ATTENUATION
        self.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MIN_SUP_ATTENUATION = (
            self.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MIN_SUP_ATTENUATION
        )

        # orders parser
        self.ORDERS_PARSER.TEST_AND_FIX_SPOT_QUANTITIES = self.ORDERS_PARSER.TEST_AND_FIX_SPOT_QUANTITIES
        self.ORDERS_PARSER.TEST_AND_FIX_FUTURES_QUANTITIES = self.ORDERS_PARSER.TEST_AND_FIX_FUTURES_QUANTITIES

        # positions parser
        self.POSITIONS_PARSER.MODE_KEY_NAMES = self.POSITIONS_PARSER.MODE_KEY_NAMES
        self.POSITIONS_PARSER.ONEWAY_VALUES = self.POSITIONS_PARSER.ONEWAY_VALUES
        self.POSITIONS_PARSER.HEDGE_VALUES = self.POSITIONS_PARSER.HEDGE_VALUES

        # ticker parser
        self.TICKER_PARSER.FUNDING_TIME_UPDATE_PERIOD = (
            self.TICKER_PARSER.FUNDING_TIME_UPDATE_PERIOD
        )

        # other
        self.FUNDING_IN_TICKER = True
        self.MARK_PRICE_IN_TICKER = True
        self.FUNDING_WITH_MARK_PRICE = True
        self.MARK_PRICE_IN_POSITION = True

        self.ADD_COST_TO_CREATE_SPOT_MARKET_ORDER = False
        self.ADD_COST_TO_CREATE_FUTURE_MARKET_ORDER = False

    def set_all_get_methods(self, exchange_connector):
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
            exchange_connector.get_positions_linear.__name__,
            exchange_connector.get_positions_inverse.__name__,
            exchange_connector.get_positions_swap.__name__,
            exchange_connector.get_positions_option.__name__,
            exchange_connector.get_positions_with_private_get_position_risk.__name__,
        ]
        self.ALL_GET_SYMBOL_POSITION_METHODS = [
            exchange_connector.get_positions_linear.__name__,
            exchange_connector.get_positions_inverse.__name__,
            exchange_connector.get_positions_swap.__name__,
            exchange_connector.get_positions_option.__name__,
        ]

    GET_ORDER_METHODS: list = None
    GET_ALL_ORDERS_METHODS: list = None
    GET_OPEN_ORDERS_METHODS: list = None
    GET_CLOSED_ORDERS_METHODS: list = None
    CANCEL_ORDERS_METHODS: list = None
    GET_MY_RECENT_TRADES_METHODS: list = None
    GET_POSITION_METHODS: list = None
    GET_SYMBOL_POSITION_METHODS: list = None
    FUNDING_IN_TICKER: bool = None
    MARK_PRICE_IN_TICKER: bool = None
    FUNDING_WITH_MARK_PRICE: bool = None
    MARK_PRICE_IN_POSITION: bool = None
    CANDLE_LOADING_LIMIT: int = None
    MAX_RECENT_TRADES_PAGINATION_LIMIT: int = None
    MAX_ORDER_PAGINATION_LIMIT: int = None
    ADD_COST_TO_CREATE_SPOT_MARKET_ORDER: bool = None
    ADD_COST_TO_CREATE_FUTURE_MARKET_ORDER: bool = None
    ALL_GET_ORDER_METHODS: list = None
    ALL_GET_ALL_ORDERS_METHODS: list = None
    ALL_GET_OPEN_ORDERS_METHODS: list = None
    ALL_GET_CLOSED_ORDERS_METHODS: list = None
    ALL_CANCEL_ORDERS_METHODS: list = None
    ALL_GET_MY_RECENT_TRADES_METHODS: list = None
    ALL_GET_POSITION_METHODS: list = None
    ALL_GET_SYMBOL_POSITION_METHODS: list = None
    POSITION_TYPES: list = None
