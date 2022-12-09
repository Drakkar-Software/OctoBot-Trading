import octobot_trading.exchanges.connectors.exchange_test_status as exchange_test_status
import octobot_trading.exchanges.parser as parser


class ExchangeConfig:
    """
    override this class if you implement a new exchange connector
    see CCXTExchangeConfig as an example
    """

    # override classes if you need a different parser
    MARKET_STATUS_PARSER: parser.ExchangeMarketStatusParser = parser.ExchangeMarketStatusParser
    ORDERS_PARSER: parser.OrdersParser = parser.OrdersParser
    TRADES_PARSER: parser.TradesParser = parser.TradesParser
    POSITIONS_PARSER: parser.PositionsParser = parser.PositionsParser
    TICKER_PARSER: parser.TickerParser = parser.TickerParser
    FUNDING_RATE_PARSER: parser.FundingRateParser = parser.FundingRateParser
    
    FUNDING_IN_TICKER: bool = False
    MARK_PRICE_IN_TICKER: bool = False
    FUNDING_WITH_MARK_PRICE: bool = False
    MARK_PRICE_IN_POSITION: bool = False

    def __init__(self, exchange_connector):
        self.set_default_settings(exchange_connector)
        self.set_connector_settings(exchange_connector)

    @classmethod
    def set_connector_settings(cls, exchange_connector) -> None:
        """
        override this method in the exchange tentacle to change default settings

        for example:
            self.MARKET_STATUS_PARSER.FIX_PRECISION = True
            self.MARK_PRICE_IN_POSITION = True
        """
        pass

    # set test status for each exchange

    IS_FULLY_TESTED_AND_SUPPORTED = False  # not recommended
    
    is_untested: exchange_test_status.ExchangeTestStatus = (
        exchange_test_status.ExchangeTestStatus()
    )
    
    CANDLE_LOADING_LIMIT_TEST_STATUS: exchange_test_status.ExchangeTestStatus = is_untested
    MAX_RECENT_TRADES_PAGINATION_LIMIT_TEST_STATUS: exchange_test_status.ExchangeTestStatus = is_untested
    MAX_ORDER_PAGINATION_LIMIT_TEST_STATUS: exchange_test_status.ExchangeTestStatus = is_untested

    MARKET_STATUS_PARSER_TEST_STATUS: exchange_test_status.ExchangeTestStatus = is_untested
    ORDERS_PARSER_TEST_STATUS: exchange_test_status.ExchangeTestStatus = is_untested
    TRADES_PARSER_TEST_STATUS: exchange_test_status.ExchangeTestStatus = is_untested
    POSITIONS_PARSER_TEST_STATUS: exchange_test_status.ExchangeTestStatus = is_untested
    TICKER_PARSER_TEST_STATUS: exchange_test_status.ExchangeTestStatus = is_untested
    FUNDING_RATE_PARSER_TEST_STATUS: exchange_test_status.ExchangeTestStatus = is_untested

    GET_ORDER_METHODS_TEST_STATUS: exchange_test_status.ExchangeTestStatus = is_untested
    GET_ALL_ORDERS_METHODS_TEST_STATUS: exchange_test_status.ExchangeTestStatus = is_untested
    GET_OPEN_ORDERS_METHODS_TEST_STATUS: exchange_test_status.ExchangeTestStatus = is_untested
    GET_CLOSED_ORDERS_METHODS_TEST_STATUS: exchange_test_status.ExchangeTestStatus = is_untested
    CANCEL_ORDERS_METHODS_TEST_STATUS: exchange_test_status.ExchangeTestStatus = is_untested
    GET_MY_RECENT_TRADES_METHODS_TEST_STATUS: exchange_test_status.ExchangeTestStatus = is_untested
    GET_POSITIONS_METHODS_TEST_STATUS: exchange_test_status.ExchangeTestStatus = is_untested
    GET_POSITION_METHODS_TEST_STATUS: exchange_test_status.ExchangeTestStatus = is_untested

    @classmethod
    def is_fully_tested_and_supported(cls):
        return cls.IS_FULLY_TESTED_AND_SUPPORTED or (
            cls.CANDLE_LOADING_LIMIT_TEST_STATUS.is_fully_tested
            and cls.MAX_RECENT_TRADES_PAGINATION_LIMIT_TEST_STATUS.is_fully_tested
            and cls.MAX_ORDER_PAGINATION_LIMIT_TEST_STATUS.is_fully_tested
            and cls.MARKET_STATUS_PARSER_TEST_STATUS.is_fully_tested
            and cls.ORDERS_PARSER_TEST_STATUS.is_fully_tested
            and cls.TRADES_PARSER_TEST_STATUS.is_fully_tested
            and cls.POSITIONS_PARSER_TEST_STATUS.is_fully_tested
            and cls.TICKER_PARSER_TEST_STATUS.is_fully_tested
            and cls.FUNDING_RATE_PARSER_TEST_STATUS.is_fully_tested
            and cls.GET_ORDER_METHODS_TEST_STATUS.is_fully_tested
            and cls.GET_ALL_ORDERS_METHODS_TEST_STATUS.is_fully_tested
            and cls.GET_OPEN_ORDERS_METHODS_TEST_STATUS.is_fully_tested
            and cls.GET_CLOSED_ORDERS_METHODS_TEST_STATUS.is_fully_tested
            and cls.CANCEL_ORDERS_METHODS_TEST_STATUS.is_fully_tested
            and cls.GET_MY_RECENT_TRADES_METHODS_TEST_STATUS.is_fully_tested
            and cls.GET_POSITIONS_METHODS_TEST_STATUS.is_fully_tested
            and cls.GET_POSITION_METHODS_TEST_STATUS.is_fully_tested
        )

    @classmethod
    def set_default_settings(cls, exchange_connector):
        """
        override to define default settings
        for example:
            cls.FUNDING_IN_TICKER = True
        
        see CCXTExchangeConfig as an example
        """
        pass
