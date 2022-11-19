from octobot_commons import enums as common_enums
from octobot_trading import enums as enums
import octobot_trading.exchanges.config.ccxt_exchange_settings as ccxt_exchange_settings


def initialize_experimental_exchange_settings(exchange, inputs):
    experimental_enabled = exchange.UI.user_input(
        "experimental_mode",
        common_enums.UserInputTypes.BOOLEAN,
        False,
        registered_inputs=inputs,
        title="Experimental mode",
    )
    if experimental_enabled:
        settings: ccxt_exchange_settings.CCXTExchangeConfig = (
            exchange.CONNECTOR_SETTINGS
        )
        experimental_settings_name = "experimental_settings"
        exchange.UI.user_input(
            experimental_settings_name,
            common_enums.UserInputTypes.OBJECT,
            def_val=None,
            registered_inputs=inputs,
            title="!!Warning: THIS MODE SHOULD NOT BE USED WITH REAL TRADER ACTIVATED!!\n"
            "While we aimed to make all available settings to: either work or interrupt with an error report, "
            "unexpected side effects might still occur\n\n"
            "This allows you to try different variants of how OctoBot talks with an exchange without the need of writing code",
        )
        settings.GET_ORDER_METHODS = exchange.UI.user_input(
            "get_order_methods",
            common_enums.UserInputTypes.MULTIPLE_OPTIONS,
            def_val=settings.GET_ORDER_METHODS,
            options=settings.ALL_GET_ORDER_METHODS,
            registered_inputs=inputs,
            title="Get order methods: Each method will be tried until OctoBot finds a single order with the requested order id",
            parent_input_name=experimental_settings_name,
        )
        settings.GET_OPEN_ORDERS_METHODS = exchange.UI.user_input(
            "get_open_orders_methods",
            common_enums.UserInputTypes.MULTIPLE_OPTIONS,
            def_val=settings.GET_OPEN_ORDERS_METHODS,
            options=settings.ALL_GET_OPEN_ORDERS_METHODS,
            registered_inputs=inputs,
            title="Get open orders methods: All methods will be used and orders will be merged and duplicates removed",
            parent_input_name=experimental_settings_name,
        )
        settings.GET_CLOSED_ORDERS_METHODS = exchange.UI.user_input(
            "get_closed_orders_methods",
            common_enums.UserInputTypes.MULTIPLE_OPTIONS,
            def_val=settings.GET_CLOSED_ORDERS_METHODS,
            options=settings.ALL_GET_CLOSED_ORDERS_METHODS,
            registered_inputs=inputs,
            title="Get closed orders methods: All methods will be used and orders will be merged and duplicates removed",
            parent_input_name=experimental_settings_name,
        )
        settings.GET_MY_RECENT_TRADES_METHODS = exchange.UI.user_input(
            "get_my_recent_trades_methods",
            common_enums.UserInputTypes.MULTIPLE_OPTIONS,
            def_val=settings.GET_MY_RECENT_TRADES_METHODS,
            options=settings.ALL_GET_MY_RECENT_TRADES_METHODS,
            registered_inputs=inputs,
            title="Get my recent trades methods: Each method will be tried until OctoBot find trades",
            parent_input_name=experimental_settings_name,
        )
        settings.CANDLE_LOADING_LIMIT = exchange.UI.user_input(
            "candle_loading_limit",
            common_enums.UserInputTypes.INT,
            def_val=settings.CANDLE_LOADING_LIMIT,
            registered_inputs=inputs,
            title="Candle pagination limit (0 is disabled): Many exchanges have a limit of how many candles we can fetch at once. "
            "(Hint: OctoBot will still be able to download candle history and automatically split it up into multiple requests)",
            parent_input_name=experimental_settings_name,
        )
        settings.MAX_RECENT_TRADES_PAGINATION_LIMIT = exchange.UI.user_input(
            "max_recent_trades_pagination_limit",
            common_enums.UserInputTypes.INT,
            def_val=settings.MAX_RECENT_TRADES_PAGINATION_LIMIT,
            registered_inputs=inputs,
            title="Recent trades pagination limit (0 is disabled): Many exchanges have a limit of how many trades we can fetch at once. "
            "(Hint: OctoBot will still be able to download trades and automatically split it up into multiple requests)",
            parent_input_name=experimental_settings_name,
        )
        settings.MAX_ORDER_PAGINATION_LIMIT = exchange.UI.user_input(
            "max_order_pagination_limit",
            common_enums.UserInputTypes.INT,
            def_val=settings.MAX_ORDER_PAGINATION_LIMIT,
            registered_inputs=inputs,
            title="Orders pagination limit (0 is disabled): Many exchanges have a limit of how many orders we can fetch at once. "
            "(Hint: OctoBot will still be able to download orders and automatically split it up into multiple requests)",
            parent_input_name=experimental_settings_name,
        )
        settings.MARKET_STATUS_FIX_PRECISION = exchange.UI.user_input(
            "market_status_fix_precision",
            common_enums.UserInputTypes.BOOLEAN,
            def_val=settings.MARKET_STATUS_FIX_PRECISION,
            registered_inputs=inputs,
            title="Fix market status precision: ",  # todo
            parent_input_name=experimental_settings_name,
        )
        settings.MARKET_STATUS_REMOVE_INVALID_PRICE_LIMITS = exchange.UI.user_input(
            "MARKET_STATUS_REMOVE_INVALID_PRICE_LIMITS",
            common_enums.UserInputTypes.BOOLEAN,
            def_val=settings.MARKET_STATUS_REMOVE_INVALID_PRICE_LIMITS,
            registered_inputs=inputs,
            title="Remove invalid price limits from market status: Some exchanges send an invalid value for the minimum and maximum position size. "
            "Which can lead to OctoBot not being able to place a trade. With this enabled, new trade sizes will not be adjusted according to minimum and maximum sizes.",  # todo
            parent_input_name=experimental_settings_name,
        )
