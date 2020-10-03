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

from octobot_trading.exchanges import channel
from octobot_trading.exchanges.channel import (
    ExchangeChannelConsumer,
    ExchangeChannelInternalConsumer,
    ExchangeChannelSupervisedConsumer,
    ExchangeChannelProducer,
    ExchangeChannel,
    TimeFrameExchangeChannel,
    set_chan,
    get_exchange_channels,
    del_exchange_channel_container,
    get_chan,
    del_chan,
    stop_exchange_channels,
    requires_refresh_trigger,
    create_exchange_channels,
    create_exchange_producers,
    create_authenticated_producer_from_parent,
)

from octobot_trading.exchanges import exchange_manager
from octobot_trading.exchanges import exchange_builder
from octobot_trading.exchanges.channel import exchange_channel
from octobot_trading.exchanges import exchange_factory
from octobot_trading.exchanges import exchanges
from octobot_trading.exchanges import exchange_util
from octobot_trading.exchanges import abstract_exchange
from octobot_trading.exchanges import exchange_websocket_factory
from octobot_trading.exchanges import exchange_config_data
from octobot_trading.exchanges import implementations
from octobot_trading.exchanges import traders
from octobot_trading.exchanges import types
from octobot_trading.exchanges import util
from octobot_trading.exchanges import websockets

from octobot_trading.exchanges.exchange_manager import (
    ExchangeManager,
)
from octobot_trading.exchanges.exchange_builder import (
    ExchangeBuilder,
    create_exchange_builder_instance,
)
from octobot_trading.exchanges.traders import (
    Trader,
    TraderSimulator,
)
from octobot_trading.exchanges.implementations import (
    ExchangeSimulator,
    SpotExchangeSimulator,
    FutureExchangeSimulator,
    MarginExchangeSimulator,
    DefaultCCXTSpotExchange,
    CCXTExchange,
    SpotCCXTExchange,
)
from octobot_trading.exchanges.types import (
    FutureExchange,
    WebsocketExchange,
    MarginExchange,
    SpotExchange,
)
from octobot_trading.exchanges.util import (
    ExchangeMarketStatusFixer,
    is_ms_valid,
    check_market_status_limits,
    check_market_status_values,
    get_markets_limit,
    calculate_amounts,
    calculate_costs,
    calculate_prices,
    fix_market_status_limits_from_current_data,
)
from octobot_trading.exchanges.websockets import (
    AbstractWebsocket,
    OctoBotWebSocketClient,
    force_disable_web_socket,
    check_web_socket_config,
    search_websocket_class,
    get_exchange_websocket_from_name,
)
from octobot_trading.exchanges.exchange_factory import (
    create_exchanges,
    create_real_exchange,
    initialize_real_exchange,
    create_simulated_exchange,
    init_simulated_exchange,
)
from octobot_trading.exchanges.exchanges import (
    ExchangeConfiguration,
    Exchanges,
)
from octobot_trading.exchanges.exchange_util import (
    get_margin_exchange_class,
    get_future_exchange_class,
    get_spot_exchange_class,
    search_exchange_class_from_exchange_name,
    get_order_side,
)
from octobot_trading.exchanges.abstract_exchange import (
    AbstractExchange,
)
from octobot_trading.exchanges.exchange_websocket_factory import (
    is_exchange_managed_by_websocket,
    is_websocket_feed_requiring_init,
    search_and_create_websocket,
)
from octobot_trading.exchanges.exchange_config_data import (
    ExchangeConfig,
)

__all__ = [
    "ExchangeConfig",
    "ExchangeManager",
    "ExchangeBuilder",
    "create_exchange_builder_instance",
    "ExchangeChannelConsumer",
    "ExchangeChannelInternalConsumer",
    "ExchangeChannelSupervisedConsumer",
    "ExchangeChannelProducer",
    "ExchangeChannel",
    "TimeFrameExchangeChannel",
    "set_chan",
    "get_exchange_channels",
    "del_exchange_channel_container",
    "get_chan",
    "del_chan",
    "stop_exchange_channels",
    "create_exchanges",
    "create_real_exchange",
    "initialize_real_exchange",
    "create_simulated_exchange",
    "init_simulated_exchange",
    "ExchangeConfiguration",
    "Exchanges",
    "get_margin_exchange_class",
    "get_future_exchange_class",
    "get_spot_exchange_class",
    "search_exchange_class_from_exchange_name",
    "get_order_side",
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
    "ExchangeSimulator",
    "SpotExchangeSimulator",
    "FutureExchangeSimulator",
    "MarginExchangeSimulator",
    "DefaultCCXTSpotExchange",
    "CCXTExchange",
    "SpotCCXTExchange",
    "FutureExchange",
    "WebsocketExchange",
    "MarginExchange",
    "SpotExchange",
    "ExchangeMarketStatusFixer",
    "is_ms_valid",
    "check_market_status_limits",
    "check_market_status_values",
    "get_markets_limit",
    "calculate_amounts",
    "calculate_costs",
    "calculate_prices",
    "fix_market_status_limits_from_current_data",
    "OctoBotWebSocketClient",
    "AbstractWebsocket",
    "force_disable_web_socket",
    "check_web_socket_config",
    "search_websocket_class",
    "get_exchange_websocket_from_name",
]
