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
    FUNDING_RATE_PARSER: parser.FundingRateParser = parser.FundingRateParser

    def __init__(self, exchange_connector):
        self.set_all_get_methods(exchange_connector)
        self.set_default_settings(exchange_connector)
        self.set_connector_settings(exchange_connector)

    @classmethod
    def set_connector_settings(cls, exchange_connector) -> None:
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
    FUNDING_RATE_PARSER_IS_FULLY_TESTED_AND_SUPPORTED = False

    GET_ORDER_METHODS_IS_FULLY_TESTED_AND_SUPPORTED = False
    GET_ALL_ORDERS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED = False
    GET_OPEN_ORDERS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED = False
    GET_CLOSED_ORDERS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED = False
    CANCEL_ORDERS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED = False
    GET_MY_RECENT_TRADES_METHODS_IS_FULLY_TESTED_AND_SUPPORTED = False
    GET_POSITION_METHODS_IS_FULLY_TESTED_AND_SUPPORTED = False
    GET_SYMBOL_POSITIONS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED = False

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
                and cls.FUNDING_RATE_PARSER_IS_FULLY_TESTED_AND_SUPPORTED
                and cls.GET_ORDER_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
                and cls.GET_ALL_ORDERS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
                and cls.GET_OPEN_ORDERS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
                and cls.GET_CLOSED_ORDERS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
                and cls.CANCEL_ORDERS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
                and cls.GET_MY_RECENT_TRADES_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
                and cls.GET_POSITION_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
                and cls.GET_SYMBOL_POSITIONS_METHODS_IS_FULLY_TESTED_AND_SUPPORTED
        )

    @classmethod
    def set_default_settings(cls, exchange_connector):
        # pagination limits
        cls.CANDLE_LOADING_LIMIT = 0
        cls.MAX_RECENT_TRADES_PAGINATION_LIMIT = 0
        cls.MAX_ORDER_PAGINATION_LIMIT = 0

        # define available get methods
        cls.GET_ORDER_METHODS = cls.ALL_GET_ORDER_METHODS
        cls.GET_ALL_ORDERS_METHODS = cls.ALL_GET_ALL_ORDERS_METHODS
        cls.GET_OPEN_ORDERS_METHODS = cls.ALL_GET_OPEN_ORDERS_METHODS
        cls.GET_CLOSED_ORDERS_METHODS = cls.ALL_GET_CLOSED_ORDERS_METHODS
        cls.CANCEL_ORDERS_METHODS = cls.ALL_CANCEL_ORDERS_METHODS
        cls.GET_MY_RECENT_TRADES_METHODS = cls.ALL_GET_MY_RECENT_TRADES_METHODS
        cls.GET_POSITION_METHODS = cls.ALL_GET_POSITION_METHODS
        cls.GET_SYMBOL_POSITION_METHODS = cls.ALL_GET_SYMBOL_POSITION_METHODS

        # market status parser
        cls.MARKET_STATUS_PARSER.FIX_PRECISION = cls.MARKET_STATUS_PARSER.FIX_PRECISION
        cls.MARKET_STATUS_PARSER.REMOVE_INVALID_PRICE_LIMITS = cls.MARKET_STATUS_PARSER.REMOVE_INVALID_PRICE_LIMITS
        cls.MARKET_STATUS_PARSER.LIMIT_PRICE_MULTIPLIER = cls.MARKET_STATUS_PARSER.LIMIT_PRICE_MULTIPLIER
        cls.MARKET_STATUS_PARSER.LIMIT_COST_MULTIPLIER = cls.MARKET_STATUS_PARSER.LIMIT_COST_MULTIPLIER
        cls.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MAX_SUP_ATTENUATION = (
            cls.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MAX_SUP_ATTENUATION
        )
        cls.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MAX_MINUS_3_ATTENUATION = (
            cls.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MAX_MINUS_3_ATTENUATION
        )
        cls.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MIN_ATTENUATION = cls.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MIN_ATTENUATION
        cls.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MIN_SUP_ATTENUATION = (
            cls.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MIN_SUP_ATTENUATION
        )

        # orders parser
        cls.ORDERS_PARSER.TEST_AND_FIX_SPOT_QUANTITIES = cls.ORDERS_PARSER.TEST_AND_FIX_SPOT_QUANTITIES
        cls.ORDERS_PARSER.TEST_AND_FIX_FUTURES_QUANTITIES = cls.ORDERS_PARSER.TEST_AND_FIX_FUTURES_QUANTITIES

        # positions parser
        cls.POSITIONS_PARSER.MODE_KEY_NAMES = cls.POSITIONS_PARSER.MODE_KEY_NAMES
        cls.POSITIONS_PARSER.ONEWAY_VALUES = cls.POSITIONS_PARSER.ONEWAY_VALUES
        cls.POSITIONS_PARSER.HEDGE_VALUES = cls.POSITIONS_PARSER.HEDGE_VALUES

        # funding rate parser
        cls.FUNDING_RATE_PARSER.FUNDING_TIME_UPDATE_PERIOD = (
            cls.FUNDING_RATE_PARSER.FUNDING_TIME_UPDATE_PERIOD
        )

        # other
        cls.FUNDING_IN_TICKER = True
        cls.MARK_PRICE_IN_TICKER = True
        cls.FUNDING_WITH_MARK_PRICE = True
        cls.MARK_PRICE_IN_POSITION = True

        cls.ADD_COST_TO_CREATE_SPOT_MARKET_ORDER = False
        cls.ADD_COST_TO_CREATE_FUTURE_MARKET_ORDER = False

    @classmethod
    def set_all_get_methods(cls, exchange_connector):
        # available methods to choose from
        cls.ALL_GET_ORDER_METHODS = [
            exchange_connector.get_order_default.__name__,
            exchange_connector.get_order_from_open_and_closed_orders.__name__,
            exchange_connector.get_order_using_stop_params.__name__,
            exchange_connector.get_trade.__name__,
        ]
        cls.ALL_GET_ALL_ORDERS_METHODS = [
            exchange_connector.get_all_orders_default.__name__,
            exchange_connector.get_all_stop_orders_using_stop_loss_params.__name__,
        ]
        cls.ALL_GET_OPEN_ORDERS_METHODS = [
            exchange_connector.get_open_orders_default.__name__,
            exchange_connector.get_open_stop_orders_using_stop_loss_params.__name__,
        ]
        cls.ALL_GET_CLOSED_ORDERS_METHODS = [
            exchange_connector.get_closed_orders_default.__name__,
            exchange_connector.get_closed_stop_orders_using_stop_loss_params.__name__,
        ]
        cls.ALL_CANCEL_ORDERS_METHODS = [
            exchange_connector.cancel_order_default.__name__,
            exchange_connector.cancel_stop_order_using_stop_loss_endpoint.__name__,
        ]
        cls.ALL_GET_MY_RECENT_TRADES_METHODS = [
            exchange_connector.get_my_recent_trades_default.__name__,
            exchange_connector.get_my_recent_trades_using_recent_trades.__name__,
            exchange_connector.get_my_recent_trades_using_closed_orders.__name__,
        ]
        cls.ALL_GET_POSITION_METHODS = [
            exchange_connector.get_positions_linear.__name__,
            exchange_connector.get_positions_inverse.__name__,
            exchange_connector.get_positions_swap.__name__,
            exchange_connector.get_positions_option.__name__,
            exchange_connector.get_positions_with_private_get_position_risk.__name__,
        ]
        cls.ALL_GET_SYMBOL_POSITION_METHODS = [
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
