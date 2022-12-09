from octobot_commons import enums as common_enums
from octobot_trading import enums as enums
import octobot_trading.exchanges.connectors.ccxt.exchange_settings_ccxt as exchange_settings_ccxt


def initialize_experimental_exchange_settings(exchange, inputs):
    settings: exchange_settings_ccxt.CCXTExchangeConfig = exchange.CONNECTOR_CONFIG
    experimental_enabled = exchange.UI.user_input(
        "experimental_mode",
        common_enums.UserInputTypes.BOOLEAN,
        False,
        registered_inputs=inputs,
        title="Experimental mode",
    )
    if experimental_enabled:
        experimental_settings_name = "experimental_settings"
        exchange.UI.user_input(
            experimental_settings_name,
            common_enums.UserInputTypes.OBJECT,
            def_val=None,
            registered_inputs=inputs,
            title="!!Warning: THIS MODE SHOULD NOT BE USED WITH REAL TRADER ACTIVATED!! "
            "While we aimed to make all available settings to: either work or interrupt with an error report, "
            "unexpected side effects might still occur. "
            "This allows you to try different variants of how OctoBot talks with an exchange without the need of writing code",
        )

        pagination_settings_name = "pagination_settings"
        exchange.UI.user_input(
            pagination_settings_name,
            common_enums.UserInputTypes.OBJECT,
            def_val=None,
            registered_inputs=inputs,
            title="Pagination limit settings",
            parent_input_name=experimental_settings_name,
        )
        if not settings.CANDLE_LOADING_LIMIT_TEST_STATUS.is_fully_tested:
            settings.CANDLE_LOADING_LIMIT = exchange.UI.user_input(
                "candle_loading_limit",
                common_enums.UserInputTypes.INT,
                def_val=settings.CANDLE_LOADING_LIMIT,
                registered_inputs=inputs,
                title="Candle pagination limit (0 is disabled): Many exchanges have a limit of how many candles we can fetch at once. "
                "(Hint: OctoBot will still be able to download candle history and automatically split it up into multiple requests)",
                parent_input_name=pagination_settings_name,
            )
        if not settings.MAX_RECENT_TRADES_PAGINATION_LIMIT_TEST_STATUS.is_fully_tested:
            settings.MAX_RECENT_TRADES_PAGINATION_LIMIT = exchange.UI.user_input(
                "max_recent_trades_pagination_limit",
                common_enums.UserInputTypes.INT,
                def_val=settings.MAX_RECENT_TRADES_PAGINATION_LIMIT,
                registered_inputs=inputs,
                title="Recent trades pagination limit (0 is disabled): Many exchanges have a limit of how many trades we can fetch at once. "
                "(Hint: OctoBot will still be able to download trades and automatically split it up into multiple requests)",
                parent_input_name=pagination_settings_name,
            )
        if not settings.MAX_ORDER_PAGINATION_LIMIT_TEST_STATUS.is_fully_tested:
            settings.MAX_ORDER_PAGINATION_LIMIT = exchange.UI.user_input(
                "max_order_pagination_limit",
                common_enums.UserInputTypes.INT,
                def_val=settings.MAX_ORDER_PAGINATION_LIMIT,
                registered_inputs=inputs,
                title="Orders pagination limit (0 is disabled): Many exchanges have a limit of how many orders we can fetch at once. "
                "(Hint: OctoBot will still be able to download orders and automatically split it up into multiple requests)",
                parent_input_name=pagination_settings_name,
            )
        market_status_parser_settings_name = "market_status_parser"
        exchange.UI.user_input(
            market_status_parser_settings_name,
            common_enums.UserInputTypes.OBJECT,
            def_val=None,
            registered_inputs=inputs,
            title="Market Status Parser Settings",
            parent_input_name=experimental_settings_name,
        )
        if not settings.MARKET_STATUS_PARSER_TEST_STATUS.is_fully_tested:
            settings.MARKET_STATUS_PARSER.FIX_PRECISION = exchange.UI.user_input(
                "fix_precision",
                common_enums.UserInputTypes.BOOLEAN,
                def_val=settings.MARKET_STATUS_PARSER.FIX_PRECISION,
                registered_inputs=inputs,
                title="Fix market status precision",  # todo
                parent_input_name=market_status_parser_settings_name,
            )
            settings.MARKET_STATUS_PARSER.REMOVE_INVALID_PRICE_LIMITS = exchange.UI.user_input(
                "remove_invalid_price_limits",
                common_enums.UserInputTypes.BOOLEAN,
                def_val=settings.MARKET_STATUS_PARSER.REMOVE_INVALID_PRICE_LIMITS,
                registered_inputs=inputs,
                title="Remove invalid price limits from market status: Some exchanges send an invalid value for the minimum and maximum position size. "
                "Which can lead to OctoBot not being able to place a trade. With this enabled, new trade sizes will not be adjusted according to minimum and maximum sizes.",  # todo
                parent_input_name=market_status_parser_settings_name,
            )
            settings.MARKET_STATUS_PARSER.LIMIT_PRICE_MULTIPLIER = (
                exchange.UI.user_input(
                    "limit_price_multiplier",
                    common_enums.UserInputTypes.INT,
                    def_val=settings.MARKET_STATUS_PARSER.LIMIT_PRICE_MULTIPLIER,
                    registered_inputs=inputs,
                    title="limit_price_multiplier",  # todo
                    parent_input_name=market_status_parser_settings_name,
                )
            )
            settings.MARKET_STATUS_PARSER.LIMIT_COST_MULTIPLIER = (
                exchange.UI.user_input(
                    "limit_cost_multiplier",
                    common_enums.UserInputTypes.INT,
                    def_val=settings.MARKET_STATUS_PARSER.LIMIT_COST_MULTIPLIER,
                    registered_inputs=inputs,
                    title="limit_cost_multiplier",  # todo
                    parent_input_name=market_status_parser_settings_name,
                )
            )
            settings.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MAX_SUP_ATTENUATION = exchange.UI.user_input(
                "limit_amount_max_sup_attenuation",
                common_enums.UserInputTypes.INT,
                def_val=settings.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MAX_SUP_ATTENUATION,
                registered_inputs=inputs,
                title="limit_amount_max_sup_attenuation",  # todo
                parent_input_name=market_status_parser_settings_name,
            )
            settings.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MAX_MINUS_3_ATTENUATION = exchange.UI.user_input(
                "limit_amount_max_minus_3_attenuation",
                common_enums.UserInputTypes.INT,
                def_val=settings.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MAX_MINUS_3_ATTENUATION,
                registered_inputs=inputs,
                title="limit_amount_max_minus_3_attenuation",  # todo
                parent_input_name=market_status_parser_settings_name,
            )
            settings.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MIN_ATTENUATION = (
                exchange.UI.user_input(
                    "limit_amount_min_attenuation",
                    common_enums.UserInputTypes.INT,
                    def_val=settings.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MIN_ATTENUATION,
                    registered_inputs=inputs,
                    title="limit_amount_min_attenuation",  # todo
                    parent_input_name=market_status_parser_settings_name,
                )
            )
            settings.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MIN_SUP_ATTENUATION = exchange.UI.user_input(
                "limit_amount_min_sup_attenuation",
                common_enums.UserInputTypes.INT,
                def_val=settings.MARKET_STATUS_PARSER.LIMIT_AMOUNT_MIN_SUP_ATTENUATION,
                registered_inputs=inputs,
                title="limit_amount_min_sup_attenuation",  # todo
                parent_input_name=market_status_parser_settings_name,
            )
        orders_parser_settings_name = "orders_parser"
        exchange.UI.user_input(
            orders_parser_settings_name,
            common_enums.UserInputTypes.OBJECT,
            def_val=None,
            registered_inputs=inputs,
            title="Orders Parser Settings",
            parent_input_name=experimental_settings_name,
        )
        if not settings.ORDERS_PARSER_TEST_STATUS.is_fully_tested:
            settings.ORDERS_PARSER.TEST_AND_FIX_SPOT_QUANTITIES = (
                exchange.UI.user_input(
                    "test_and_fix_spot_quantities",
                    common_enums.UserInputTypes.BOOLEAN,
                    def_val=settings.ORDERS_PARSER.TEST_AND_FIX_SPOT_QUANTITIES,
                    registered_inputs=inputs,
                    title="test_and_fix_spot_quantities",  # todo
                    parent_input_name=orders_parser_settings_name,
                )
            )
            settings.ORDERS_PARSER.TEST_AND_FIX_FUTURES_QUANTITIES = (
                exchange.UI.user_input(
                    "test_and_fix_futures_quantities",
                    common_enums.UserInputTypes.BOOLEAN,
                    def_val=settings.ORDERS_PARSER.TEST_AND_FIX_FUTURES_QUANTITIES,
                    registered_inputs=inputs,
                    title="test_and_fix_futures_quantities",  # todo
                    parent_input_name=orders_parser_settings_name,
                )
            )
        ticker_parser_settings_name = "ticker_parser"
        exchange.UI.user_input(
            ticker_parser_settings_name,
            common_enums.UserInputTypes.OBJECT,
            def_val=None,
            registered_inputs=inputs,
            title="Funding rate parser settings",
            parent_input_name=experimental_settings_name,
        )
        if not settings.FUNDING_RATE_PARSER_TEST_STATUS.is_fully_tested:
            settings.FUNDING_RATE_PARSER.FUNDING_TIME_UPDATE_PERIOD = exchange.UI.user_input(
                "funding_time_update_period",
                common_enums.UserInputTypes.INT,
                def_val=settings.FUNDING_RATE_PARSER.FUNDING_TIME_UPDATE_PERIOD,
                registered_inputs=inputs,
                title="Funding time update period: Time in seconds between funding rate updates. "
                "For example every 8 hours would be 28800 seconds (8 x 3600)",
                parent_input_name=ticker_parser_settings_name,
            )
        get_methods_settings_name = "get_methods_settings"
        exchange.UI.user_input(
            get_methods_settings_name,
            common_enums.UserInputTypes.OBJECT,
            def_val=None,
            registered_inputs=inputs,
            title="Get methods settings",
            parent_input_name=experimental_settings_name,
        )
        if not settings.GET_ORDER_METHODS_TEST_STATUS.is_fully_tested:
            settings.GET_ORDER_METHODS = exchange.UI.user_input(
                "get_order_methods",
                common_enums.UserInputTypes.MULTIPLE_OPTIONS,
                def_val=settings.GET_ORDER_METHODS,
                options=settings.ALL_GET_ORDER_METHODS,
                registered_inputs=inputs,
                title="Get order methods: Each method will be tried until OctoBot finds a single order with the requested order id",
                parent_input_name=get_methods_settings_name,
            )
        if not settings.GET_OPEN_ORDERS_METHODS_TEST_STATUS.is_fully_tested:
            settings.GET_OPEN_ORDERS_METHODS = exchange.UI.user_input(
                "get_open_orders_methods",
                common_enums.UserInputTypes.MULTIPLE_OPTIONS,
                def_val=settings.GET_OPEN_ORDERS_METHODS,
                options=settings.ALL_GET_OPEN_ORDERS_METHODS,
                registered_inputs=inputs,
                title="Get open orders methods: All methods will be used and orders will be merged and duplicates removed",
                parent_input_name=get_methods_settings_name,
            )
        if not settings.GET_CLOSED_ORDERS_METHODS_TEST_STATUS.is_fully_tested:
            settings.GET_CLOSED_ORDERS_METHODS = exchange.UI.user_input(
                "get_closed_orders_methods",
                common_enums.UserInputTypes.MULTIPLE_OPTIONS,
                def_val=settings.GET_CLOSED_ORDERS_METHODS,
                options=settings.ALL_GET_CLOSED_ORDERS_METHODS,
                registered_inputs=inputs,
                title="Get closed orders methods: All methods will be used and orders will be merged and duplicates removed",
                parent_input_name=get_methods_settings_name,
            )
        if not settings.GET_MY_RECENT_TRADES_METHODS_TEST_STATUS.is_fully_tested:
            settings.GET_MY_RECENT_TRADES_METHODS = exchange.UI.user_input(
                "get_my_recent_trades_methods",
                common_enums.UserInputTypes.MULTIPLE_OPTIONS,
                def_val=settings.GET_MY_RECENT_TRADES_METHODS,
                options=settings.ALL_GET_MY_RECENT_TRADES_METHODS,
                registered_inputs=inputs,
                title="Get my recent trades methods: Each method will be tried until OctoBot find trades",
                parent_input_name=get_methods_settings_name,
            )
