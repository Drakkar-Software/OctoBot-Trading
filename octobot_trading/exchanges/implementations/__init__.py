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


from octobot_trading.exchanges.implementations.cryptofeed_websocket_exchange import (
    CryptofeedWebSocketExchange,
)
from octobot_trading.exchanges.implementations import spot_exchange_simulator
from octobot_trading.exchanges.implementations.spot_exchange_simulator import (
    SpotExchangeSimulator,
)
from octobot_trading.exchanges.implementations import future_exchange_simulator
from octobot_trading.exchanges.implementations.future_exchange_simulator import (
    FutureExchangeSimulator,
)
from octobot_trading.exchanges.implementations import future_ccxt_exchange
from octobot_trading.exchanges.implementations.future_ccxt_exchange import (
    FutureCCXTExchange,
)
from octobot_trading.exchanges.implementations import margin_exchange_simulator
from octobot_trading.exchanges.implementations.margin_exchange_simulator import (
    MarginExchangeSimulator,
)
from octobot_trading.exchanges.implementations import margin_ccxt_exchange
from octobot_trading.exchanges.implementations.margin_ccxt_exchange import (
    MarginCCXTExchange,
)
from octobot_trading.exchanges.implementations import spot_ccxt_exchange
from octobot_trading.exchanges.implementations.spot_ccxt_exchange import (
    SpotCCXTExchange,
)
from octobot_trading.exchanges.implementations import ccxt_websocket_exchange
from octobot_trading.exchanges.implementations.ccxt_websocket_exchange import (
    CCXTWebSocketExchange,
)
from octobot_trading.exchanges.implementations import default_spot_ccxt_exchange
from octobot_trading.exchanges.implementations.default_spot_ccxt_exchange import (
    DefaultCCXTSpotExchange,
)
from octobot_trading.exchanges.implementations import cryptofeed_websocket_exchange
from octobot_trading.exchanges.implementations.cryptofeed_websocket_exchange import (
    CryptofeedWebSocketExchange,
)

__all__ = [
    "SpotExchangeSimulator",
    "FutureExchangeSimulator",
    "MarginExchangeSimulator",
    "FutureCCXTExchange",
    "MarginCCXTExchange",
    "SpotCCXTExchange",
    "CCXTWebSocketExchange",
    "DefaultCCXTSpotExchange",
    "CryptofeedWebSocketExchange",
]
