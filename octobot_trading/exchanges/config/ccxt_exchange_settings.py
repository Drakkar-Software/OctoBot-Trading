from octobot_commons import enums as common_enums
from octobot_trading import enums as enums
from octobot_trading.exchanges.util import parser
import octobot_trading.exchanges.util.exchange_market_status_fixer as exchange_market_status_fixer


class CCXTExchangeConfig:
    """
    override this class if you need custom settings
    """

    # available methods to choose from
    ALL_GET_ORDER_METHODS = [
        enums.CCXTExchangeConfigMethods.GET_ORDER_DEFAULT.value,
        enums.CCXTExchangeConfigMethods.GET_ORDER_PRIVATE.value,
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

    # overwrite classes if you need a different parser
    ORDERS_PARSER_CLASS = parser.OrdersParser
    TRADES_PARSER_CLASS = parser.TradesParser
    POSITIONS_PARSER_CLASS = parser.PositionsParser
    MARKET_STATUS_FIXER = exchange_market_status_fixer.ExchangeMarketStatusFixer
    
    USE_FIXED_MARKET_STATUS = None  # None -> default is with fixed market status (but without precision fixing)
    #                                 False -> define False if not necessary
    #                                 True -> set to True if exchange is know to need fixed market status (with precision fixing)

    MARKET_STATUS_FIXER_REMOVE_PRICE_LIMITS = False
    
    CANDLE_LOADING_LIMIT = 0
    MAX_RECENT_TRADES_PAGINATION_LIMIT = 0
    MAX_ORDER_PAGINATION_LIMIT = 0

    GET_ORDER_METHODS = [
        enums.CCXTExchangeConfigMethods.GET_ORDER_DEFAULT.value,
        enums.CCXTExchangeConfigMethods.GET_ORDER_PRIVATE.value,
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


def initialize_experimental_exchange_settings(exchange, inputs):
    experimental_enabled = exchange.UI.user_input(
        "experimental_mode",
        common_enums.UserInputTypes.BOOLEAN,
        False,
        inputs,
        title="Experimental mode",
    )
    if experimental_enabled:
        settings: CCXTExchangeConfig = exchange.CONNECTOR_SETTINGS
        experimental_settings_name = "experimental_settings"
        settings.GET_ORDER_METHODS = exchange.UI.user_input(
            experimental_settings_name,
            common_enums.UserInputTypes.OBJECT,
            inputs=inputs,
            title="Experimental mode:\n"
            "!!Warning: THIS MODE SHOULD NOT BE USED WITH REAL TRADER ACTIVATED!!\n"
            "While we aimed to make all available settings to: either work or interrupt with an error report, "
            "unexpected side effects might still occur\n\n"
            "This allows you to try different variants of how OctoBot talks with an exchange without the need of writing code",
            parent_input_name=experimental_settings_name,
        )
        settings.GET_ORDER_METHODS = exchange.UI.user_input(
            "get_order_methods",
            common_enums.UserInputTypes.MULTIPLE_OPTIONS,
            settings.GET_ORDER_METHODS[0],
            options=settings.ALL_GET_ORDER_METHODS,
            inputs=inputs,
            title="Get order methods: Each method will be tried until OctoBot finds a single order with the requested order id",
            parent_input_name=experimental_settings_name,
        )
        settings.GET_OPEN_ORDERS_METHODS = exchange.UI.user_input(
            "get_open_orders_methods",
            common_enums.UserInputTypes.MULTIPLE_OPTIONS,
            settings.GET_OPEN_ORDERS_METHODS[0],
            options=settings.ALL_GET_OPEN_ORDERS_METHODS,
            inputs=inputs,
            title="Get open orders methods: All methods will be used and orders will be merged and duplicates removed",
            parent_input_name=experimental_settings_name,
        )
        settings.GET_CLOSED_ORDERS_METHODS = exchange.UI.user_input(
            "get_closed_orders_methods",
            common_enums.UserInputTypes.MULTIPLE_OPTIONS,
            settings.GET_CLOSED_ORDERS_METHODS[0],
            options=settings.ALL_GET_CLOSED_ORDERS_METHODS,
            inputs=inputs,
            title="Get closed orders methods: All methods will be used and orders will be merged and duplicates removed",
            parent_input_name=experimental_settings_name,
        )
        settings.GET_MY_RECENT_TRADES_METHODS = exchange.UI.user_input(
            "get_my_recent_trades_methods",
            common_enums.UserInputTypes.MULTIPLE_OPTIONS,
            settings.GET_MY_RECENT_TRADES_METHODS[0],
            options=settings.ALL_GET_MY_RECENT_TRADES_METHODS,
            inputs=inputs,
            title="Get my recent trades methods: Each method will be tried until OctoBot find trades",
            parent_input_name=experimental_settings_name,
        )
        settings.CANDLE_LOADING_LIMIT = exchange.UI.user_input(
            "candle_loading_limit",
            common_enums.UserInputTypes.INT,
            settings.CANDLE_LOADING_LIMIT,
            inputs=inputs,
            title="Candle pagination limit (0 is disabled): Many exchanges have a limit of how many candles we can fetch at once. "
            "(Hint: OctoBot will still be able to download candle history and automatically split it up into multiple requests)",
            parent_input_name=experimental_settings_name,
        )
        settings.MAX_RECENT_TRADES_PAGINATION_LIMIT = exchange.UI.user_input(
            "max_recent_trades_pagination_limit",
            common_enums.UserInputTypes.INT,
            settings.MAX_RECENT_TRADES_PAGINATION_LIMIT,
            inputs=inputs,
            title="Recent trades pagination limit (0 is disabled): Many exchanges have a limit of how many trades we can fetch at once. "
            "(Hint: OctoBot will still be able to download trades and automatically split it up into multiple requests)",
            parent_input_name=experimental_settings_name,
        )
        settings.MAX_ORDER_PAGINATION_LIMIT = exchange.UI.user_input(
            "max_order_pagination_limit",
            common_enums.UserInputTypes.INT,
            settings.MAX_ORDER_PAGINATION_LIMIT,
            inputs=inputs,
            title="Orders pagination limit (0 is disabled): Many exchanges have a limit of how many orders we can fetch at once. "
            "(Hint: OctoBot will still be able to download orders and automatically split it up into multiple requests)",
            parent_input_name=experimental_settings_name,
        )
        settings.USE_FIXED_MARKET_STATUS = exchange.UI.user_input(
            "use_fixed_market_status",
            common_enums.UserInputTypes.BOOLEAN,
            False,
            inputs,
            title="Fix market status",  # todo
        )
        if settings.USE_FIXED_MARKET_STATUS:
            settings.MARKET_STATUS_FIXER_REMOVE_PRICE_LIMITS = exchange.UI.user_input(
                "market_status_fixer_remove_price_limits",
                common_enums.UserInputTypes.BOOLEAN,
                False,
                inputs,
                title="Market status fixer remove price limits",  # todo
            )
