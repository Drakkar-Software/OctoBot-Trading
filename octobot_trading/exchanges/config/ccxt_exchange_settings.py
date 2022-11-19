from octobot_trading import enums as enums
import octobot_trading.exchanges.parser as parser


class CCXTExchangeConfig:
    """
    override this class if you need custom settings
    """

    # available methods to choose from
    ALL_GET_ORDER_METHODS = [
        enums.CCXTExchangeConfigMethods.GET_ORDER_DEFAULT.value,
        enums.CCXTExchangeConfigMethods.GET_ORDER_FROM_OPEN_AND_CLOSED_ORDERS.value,
        enums.CCXTExchangeConfigMethods.GET_ORDER_USING_STOP_ID.value,
        enums.CCXTExchangeConfigMethods.GET_ORDER_FROM_TRADES.value,
    ]
    ALL_GET_ALL_ORDERS_METHODS = [
        enums.CCXTExchangeConfigMethods.GET_ALL_ORDERS_DEFAULT.value,
        enums.CCXTExchangeConfigMethods.GET_ALL_STOP_ORDERS_USING_STOP_LOSS_ENDPOINT.value,
    ]
    ALL_GET_OPEN_ORDERS_METHODS = [
        enums.CCXTExchangeConfigMethods.GET_OPEN_ORDERS_DEFAULT.value,
        enums.CCXTExchangeConfigMethods.GET_OPEN_STOP_ORDERS_USING_STOP_LOSS_ENDPOINT.value,
    ]
    ALL_GET_CLOSED_ORDERS_METHODS = [
        enums.CCXTExchangeConfigMethods.GET_CLOSED_ORDERS_DEFAULT.value,
        enums.CCXTExchangeConfigMethods.GET_CLOSED_STOP_ORDERS_USING_STOP_LOSS_ENDPOINT.value,
    ]
    ALL_CANCEL_ORDERS_METHODS = [
        enums.CCXTExchangeConfigMethods.CANCEL_ORDER_DEFAULT.value,
        enums.CCXTExchangeConfigMethods.CANCEL_STOP_ORDER_USING_STOP_LOSS_ENDPOINT.value,
    ]
    ALL_GET_MY_RECENT_TRADES_METHODS = [
        enums.CCXTExchangeConfigMethods.GET_MY_RECENT_TRADES_DEFAULT.value,
        enums.CCXTExchangeConfigMethods.GET_MY_RECENT_TRADES_USING_RECENT_TRADES.value,
        enums.CCXTExchangeConfigMethods.GET_MY_RECENT_TRADES_USING_CLOSED_ORDERS.value,
    ]
    ALL_GET_POSITION_METHODS = [
        enums.CCXTExchangeConfigMethods.GET_POSITION_DEFAULT.value,
        enums.CCXTExchangeConfigMethods.GET_POSITION_BY_SUB_TYPE.value,
        enums.CCXTExchangeConfigMethods.GET_POSITION_WITH_PRIVATE_GET_POSITION_RISK.value,
    ]

    # set default exchange config here

    # override classes if you need a different parser
    ORDERS_PARSER_CLASS = parser.OrdersParser
    TRADES_PARSER_CLASS = parser.TradesParser
    POSITIONS_PARSER_CLASS = parser.PositionsParser
    TICKER_PARSER_CLASS = parser.TickerParser()
    MARKET_STATUS_PARSER_CLASS = parser.ExchangeMarketStatusParser

    MARKET_STATUS_FIX_PRECISION = False
    MARKET_STATUS_REMOVE_INVALID_PRICE_LIMITS = False

    CANDLE_LOADING_LIMIT = 0
    MAX_RECENT_TRADES_PAGINATION_LIMIT = 0
    MAX_ORDER_PAGINATION_LIMIT = 0

    GET_ORDER_METHODS = [
        enums.CCXTExchangeConfigMethods.GET_ORDER_DEFAULT.value,
        enums.CCXTExchangeConfigMethods.GET_ORDER_FROM_OPEN_AND_CLOSED_ORDERS.value,
        enums.CCXTExchangeConfigMethods.GET_ORDER_USING_STOP_ID.value,
        enums.CCXTExchangeConfigMethods.GET_ORDER_FROM_TRADES.value,
    ]
    GET_ALL_ORDERS_METHODS = [
        enums.CCXTExchangeConfigMethods.GET_ALL_ORDERS_DEFAULT.value,
        enums.CCXTExchangeConfigMethods.GET_ALL_STOP_ORDERS_USING_STOP_LOSS_ENDPOINT.value,
    ]
    GET_OPEN_ORDERS_METHODS = [
        enums.CCXTExchangeConfigMethods.GET_OPEN_ORDERS_DEFAULT.value,
        enums.CCXTExchangeConfigMethods.GET_OPEN_STOP_ORDERS_USING_STOP_LOSS_ENDPOINT.value,
    ]
    GET_CLOSED_ORDERS_METHODS = [
        enums.CCXTExchangeConfigMethods.GET_CLOSED_ORDERS_DEFAULT.value,
        enums.CCXTExchangeConfigMethods.GET_CLOSED_STOP_ORDERS_USING_STOP_LOSS_ENDPOINT.value,
    ]
    CANCEL_ORDERS_METHODS = [
        enums.CCXTExchangeConfigMethods.CANCEL_ORDER_DEFAULT.value,
        enums.CCXTExchangeConfigMethods.CANCEL_STOP_ORDER_USING_STOP_LOSS_ENDPOINT.value,
    ]
    GET_MY_RECENT_TRADES_METHODS = [
        enums.CCXTExchangeConfigMethods.GET_MY_RECENT_TRADES_DEFAULT.value,
        enums.CCXTExchangeConfigMethods.GET_MY_RECENT_TRADES_USING_RECENT_TRADES.value,
        enums.CCXTExchangeConfigMethods.GET_MY_RECENT_TRADES_USING_CLOSED_ORDERS.value,
    ]
    GET_POSITION_METHODS = [
        enums.CCXTExchangeConfigMethods.GET_POSITION_DEFAULT.value,
        enums.CCXTExchangeConfigMethods.GET_POSITION_BY_SUB_TYPE.value,
        enums.CCXTExchangeConfigMethods.GET_POSITION_WITH_PRIVATE_GET_POSITION_RISK.value,
    ]
