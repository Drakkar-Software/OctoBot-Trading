#  Drakkar-Software OctoBot-Trading
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
from octobot_trading.exchanges import adapters
from octobot_trading.exchanges.adapters import (
    AbstractAdapter,
)
from octobot_trading.exchanges import exchanges
from octobot_trading.exchanges.exchanges import (
    ExchangeConfiguration,
    Exchanges,
)
from octobot_trading.exchanges import exchange_channels
from octobot_trading.exchanges.exchange_channels import (
    requires_refresh_trigger,
    create_exchange_channels,
    create_exchange_producers,
    create_authenticated_producer_from_parent,
)

from octobot_trading.exchanges import abstract_exchange
from octobot_trading.exchanges.abstract_exchange import (
    AbstractExchange,
)

from octobot_trading.exchanges import abstract_websocket_exchange
from octobot_trading.exchanges.abstract_websocket_exchange import (
    AbstractWebsocketExchange,
)

from octobot_trading.exchanges import basic_exchange_wrapper
from octobot_trading.exchanges.basic_exchange_wrapper import (
    BasicExchangeWrapper,
    temporary_exchange_wrapper,
)

from octobot_trading.exchanges import exchange_manager
from octobot_trading.exchanges.exchange_manager import (
    ExchangeManager,
)

from octobot_trading.exchanges import exchange_factory
from octobot_trading.exchanges.exchange_factory import (
    create_exchanges,
    create_real_exchange,
    initialize_real_exchange,
    create_simulated_exchange,
    init_simulated_exchange,
)
from octobot_trading.exchanges.util import (
    ExchangeMarketStatusFixer,
    is_ms_valid,
    get_rest_exchange_class,
    get_order_side,
    log_time_sync_error,
    get_partners_explanation_message,
    get_enabled_exchanges,
    is_compatible_account,
    get_historical_ohlcv,
    get_exchange_type,
    get_default_exchange_type,
    get_supported_exchange_types,
    update_raw_order_from_raw_trade,
    is_missing_trading_fees,
    apply_trades_fees,
    get_exchange_class_from_name,
    force_disable_web_socket,
    check_web_socket_config,
    search_websocket_class,
    supports_websocket,
)
from octobot_trading.exchanges import exchange_websocket_factory
from octobot_trading.exchanges.exchange_websocket_factory import (
    is_exchange_managed_by_websocket,
    is_websocket_feed_requiring_init,
    search_and_create_websocket,
)
from octobot_trading.exchanges import config
from octobot_trading.exchanges.config import (
    ExchangeConfig,
    BacktestingExchangeConfig,
)
from octobot_trading.exchanges import traders
from octobot_trading.exchanges.traders import (
    Trader,
    TraderSimulator,
)
from octobot_trading.exchanges import types
from octobot_trading.exchanges.types import (
    WebSocketExchange,
    RestExchange,
)
from octobot_trading.exchanges import implementations
from octobot_trading.exchanges.implementations import (
    DefaultWebSocketExchange,
    ExchangeSimulator,
    DefaultRestExchange,
)
from octobot_trading.exchanges import exchange_builder
from octobot_trading.exchanges.exchange_builder import (
    ExchangeBuilder,
    create_exchange_builder_instance,
)
from octobot_trading.exchanges import connectors
from octobot_trading.exchanges.connectors import (
    CCXTWebsocketConnector,
    CCXTConnector,
    CCXTAdapter,
    ExchangeSimulatorConnector,
    ExchangeSimulatorAdapter,
)

__all__ = [
    "AbstractAdapter",
    "ExchangeConfig",
    "BacktestingExchangeConfig",
    "ExchangeManager",
    "ExchangeBuilder",
    "create_exchange_builder_instance",
    "create_exchanges",
    "create_real_exchange",
    "initialize_real_exchange",
    "create_simulated_exchange",
    "init_simulated_exchange",
    "ExchangeConfiguration",
    "Exchanges",
    "get_rest_exchange_class",
    "get_order_side",
    "log_time_sync_error",
    "get_partners_explanation_message",
    "get_enabled_exchanges",
    "is_compatible_account",
    "get_historical_ohlcv",
    "get_exchange_type",
    "get_default_exchange_type",
    "get_supported_exchange_types",
    "update_raw_order_from_raw_trade",
    "is_missing_trading_fees",
    "apply_trades_fees",
    "get_exchange_class_from_name",
    "AbstractExchange",
    "is_exchange_managed_by_websocket",
    "is_websocket_feed_requiring_init",
    "search_and_create_websocket",
    "requires_refresh_trigger",
    "create_exchange_channels",
    "create_exchange_producers",
    "create_authenticated_producer_from_parent",
    "TraderSimulator",
    "Trader",
    "DefaultWebSocketExchange",
    "DefaultRestExchange",
    "ExchangeSimulator",
    "CCXTWebsocketConnector",
    "WebSocketExchange",
    "RestExchange",
    "ExchangeMarketStatusFixer",
    "is_ms_valid",
    "AbstractWebsocketExchange",
    "BasicExchangeWrapper",
    "temporary_exchange_wrapper",
    "force_disable_web_socket",
    "check_web_socket_config",
    "search_websocket_class",
    "supports_websocket",
    "CCXTConnector",
    "CCXTAdapter",
    "ExchangeSimulatorConnector",
    "ExchangeSimulatorAdapter",
]
