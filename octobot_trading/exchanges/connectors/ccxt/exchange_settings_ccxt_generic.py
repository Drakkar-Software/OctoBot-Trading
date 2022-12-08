import octobot_trading.exchanges.connectors.ccxt.exchange_settings_ccxt as exchange_settings_ccxt
import octobot_trading.exchanges.parser as parser
import octobot_trading.exchanges.parser.util as parser_util


class GenericCCXTExchangeConfig(exchange_settings_ccxt.CCXTExchangeConfig):
    """
    dont override this class, use CCXTExchangeConfig or ExchangeConfig as a base instead
    """

    ORDERS_PARSER: parser_util.Parser = parser.GenericCCXTOrdersParser
    TRADES_PARSER: parser_util.Parser = parser.GenericCCXTTradesParser
    POSITIONS_PARSER: parser_util.Parser = parser.GenericCCXTPositionsParser
    TICKER_PARSER: parser_util.Parser = parser.GenericCCXTTickerParser
    FUNDING_RATE_PARSER: parser_util.Parser = parser.GenericCCXTFundingRateParser

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
        cls.GET_POSITION_METHODS = cls.ALL_GET_POSITION_METHODS

        # market status parser
        cls.MARKET_STATUS_PARSER.FIX_PRECISION = cls.MARKET_STATUS_PARSER.FIX_PRECISION
        cls.MARKET_STATUS_PARSER.REMOVE_INVALID_PRICE_LIMITS = (
            cls.MARKET_STATUS_PARSER.REMOVE_INVALID_PRICE_LIMITS
        )
        cls.MARKET_STATUS_PARSER.LIMIT_PRICE_MULTIPLIER = (
            cls.MARKET_STATUS_PARSER.LIMIT_PRICE_MULTIPLIER
        )
        cls.MARKET_STATUS_PARSER.LIMIT_COST_MULTIPLIER = (
            cls.MARKET_STATUS_PARSER.LIMIT_COST_MULTIPLIER
        )
        cls.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MAX_SUP_ATTENUATION = (
            cls.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MAX_SUP_ATTENUATION
        )
        cls.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MAX_MINUS_3_ATTENUATION = (
            cls.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MAX_MINUS_3_ATTENUATION
        )
        cls.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MIN_ATTENUATION = (
            cls.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MIN_ATTENUATION
        )
        cls.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MIN_SUP_ATTENUATION = (
            cls.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MIN_SUP_ATTENUATION
        )

        # orders parser
        cls.ORDERS_PARSER.TEST_AND_FIX_SPOT_QUANTITIES = (
            cls.ORDERS_PARSER.TEST_AND_FIX_SPOT_QUANTITIES
        )
        cls.ORDERS_PARSER.TEST_AND_FIX_FUTURES_QUANTITIES = (
            cls.ORDERS_PARSER.TEST_AND_FIX_FUTURES_QUANTITIES
        )

        # positions parser
        cls.POSITIONS_PARSER.MODE_KEYS = cls.POSITIONS_PARSER.MODE_KEYS
        cls.POSITIONS_PARSER.ONEWAY_VALUES = cls.POSITIONS_PARSER.ONEWAY_VALUES
        cls.POSITIONS_PARSER.HEDGE_VALUES = cls.POSITIONS_PARSER.HEDGE_VALUES

        # funding rate parser
        cls.FUNDING_RATE_PARSER.FUNDING_TIME_UPDATE_PERIOD = (
            cls.FUNDING_RATE_PARSER.FUNDING_TIME_UPDATE_PERIOD
        )

        # get_positions
        cls.GET_POSITION_LINEAR_SETTLE_COINS: list = ["USDT", "USDC"]
        cls.GET_POSITION_INVERSE_SETTLE_COINS: list = [
            "BTC",
            "ETH",
            "MANA",
            "XRP",
            "ADA",
            "DOT",
            "EOS",
            "LTC",
        ]

        # other
        cls.FUNDING_IN_TICKER = True
        cls.MARK_PRICE_IN_TICKER = True
        cls.FUNDING_WITH_MARK_PRICE = True
        cls.MARK_PRICE_IN_POSITION = True

        cls.ADD_COST_TO_CREATE_SPOT_MARKET_ORDER = False
        cls.ADD_COST_TO_CREATE_FUTURE_MARKET_ORDER = False
