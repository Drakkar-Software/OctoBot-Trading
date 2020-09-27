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
from octobot_trading.exchanges import abstract_exchange
from octobot_trading.exchanges import data
from octobot_trading.exchanges import exchange_builder
from octobot_trading.exchanges import exchange_channels
from octobot_trading.exchanges import exchange_factory
from octobot_trading.exchanges import exchange_manager
from octobot_trading.exchanges import exchange_util
from octobot_trading.exchanges import exchange_websocket_factory
from octobot_trading.exchanges import exchanges
from octobot_trading.exchanges import types
from octobot_trading.exchanges import util
from octobot_trading.exchanges import websockets

from octobot_trading.exchanges.abstract_exchange import (AbstractExchange, )
from octobot_trading.exchanges.data import (ExchangeConfig,
                                            ExchangePersonalData,
                                            ExchangeSymbolData,
                                            ExchangeSymbolsData,
                                            exchange_config_data,
                                            exchange_personal_data,
                                            exchange_symbol_data,
                                            exchange_symbols_data, )
from octobot_trading.exchanges.exchange_builder import (ExchangeBuilder, )
from octobot_trading.exchanges.exchange_channels import (requires_refresh_trigger,
                                                         create_exchange_producers,
                                                         create_authenticated_producer_from_parent,
                                                         create_exchange_channels, )
from octobot_trading.exchanges.exchange_factory import (create_exchanges, create_real_exchange,
                                                        initialize_real_exchange, create_simulated_exchange,
                                                        init_simulated_exchange, )
from octobot_trading.exchanges.exchange_manager import (ExchangeManager, )
from octobot_trading.exchanges.exchange_util import (get_future_exchange_class,
                                                     get_margin_exchange_class,
                                                     get_order_side,
                                                     get_spot_exchange_class,
                                                     search_exchange_class_from_exchange_name, )
from octobot_trading.exchanges.exchange_websocket_factory import (is_exchange_managed_by_websocket,
                                                                  search_and_create_websocket,
                                                                  is_websocket_feed_requiring_init, )
from octobot_trading.exchanges.exchanges import (ExchangeConfiguration,
                                                 Exchanges, )
from octobot_trading.exchanges.types import (FutureExchange, MarginExchange,
                                             SpotExchange, WebsocketExchange,
                                             future_exchange, margin_exchange,
                                             spot_exchange,
                                             websocket_exchange, )
from octobot_trading.exchanges.util import (ExchangeMarketStatusFixer,
                                            calculate_amounts, calculate_costs,
                                            calculate_prices,
                                            check_market_status_limits,
                                            check_market_status_values,
                                            exchange_market_status_fixer,
                                            fix_market_status_limits_from_current_data,
                                            get_markets_limit, is_ms_valid, )
from octobot_trading.exchanges.websockets import (AbstractWebsocket,
                                                  OctoBotWebSocketClient,
                                                  abstract_websocket,
                                                  check_web_socket_config,
                                                  force_disable_web_socket,
                                                  get_exchange_websocket_from_name,
                                                  octobot_websocket,
                                                  search_websocket_class,
                                                  websockets_util, )

from octobot_trading.exchanges import implementations
from octobot_trading.exchanges.implementations import (CCXTExchange,
                                                       DefaultCCXTSpotExchange,
                                                       ExchangeSimulator,
                                                       FutureExchangeSimulator,
                                                       MarginExchangeSimulator,
                                                       SpotCCXTExchange,
                                                       SpotExchangeSimulator,
                                                       ccxt_exchange,
                                                       default_spot_ccxt,
                                                       exchange_simulator,
                                                       future_exchange_simulator,
                                                       margin_exchange_simulator,
                                                       spot_ccxt_exchange,
                                                       spot_exchange_simulator, )

__all__ = ['AbstractExchange', 'AbstractWebsocket', 'CCXTExchange',
           'DefaultCCXTSpotExchange', 'ExchangeBuilder', 'ExchangeConfig',
           'ExchangeConfiguration', 'ExchangeManager',
           'ExchangeMarketStatusFixer', 'ExchangePersonalData',
           'ExchangeSimulator', 'ExchangeSymbolData', 'ExchangeSymbolsData',
           'Exchanges', 'FutureExchange', 'FutureExchangeSimulator',
           'MarginExchange', 'MarginExchangeSimulator',
           'OctoBotWebSocketClient', 'SpotCCXTExchange', 'SpotExchange',
           'SpotExchangeSimulator', 'WebsocketExchange', 'abstract_exchange',
           'abstract_websocket', 'calculate_amounts', 'calculate_costs',
           'calculate_prices', 'ccxt_exchange', 'check_market_status_limits',
           'check_market_status_values', 'check_web_socket_config', 'data',
           'default_spot_ccxt', 'exchange_builder', 'exchange_channels',
           'exchange_config_data', 'exchange_factory', 'exchange_manager',
           'exchange_market_status_fixer', 'exchange_personal_data',
           'exchange_simulator', 'exchange_symbol_data',
           'exchange_symbols_data', 'exchange_util',
           'exchange_websocket_factory', 'exchanges',
           'fix_market_status_limits_from_current_data',
           'force_disable_web_socket', 'future_exchange', 'future_exchange_simulator',
           'get_exchange_websocket_from_name', 'get_future_exchange_class',
           'get_margin_exchange_class', 'get_markets_limit', 'get_order_side',
           'get_spot_exchange_class', 'implementations', 'is_ms_valid',
           'margin_exchange', 'margin_exchange_simulator',
           'octobot_websocket', 'create_authenticated_producer_from_parent',
           'requires_refresh_trigger', 'create_exchange_producers', 'create_exchange_channels',
           'search_exchange_class_from_exchange_name',
           'search_websocket_class',
           'create_exchanges', 'create_real_exchange', 'initialize_real_exchange',
           'create_simulated_exchange', 'init_simulated_exchange',
           'spot_exchange', 'spot_exchange_simulator', 'spot_ccxt_exchange',
           'types', 'util', 'websocket_exchange', 'websockets',
           'is_exchange_managed_by_websocket', 'search_and_create_websocket', 'is_websocket_feed_requiring_init',
           'websockets_util']
