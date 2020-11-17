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

from octobot_trading.exchanges.types import spot_exchange
from octobot_trading.exchanges.types.spot_exchange import (
    SpotExchange,
)
from octobot_trading.exchanges.types import margin_exchange
from octobot_trading.exchanges.types.margin_exchange import (
    MarginExchange,
)
from octobot_trading.exchanges.types import future_exchange
from octobot_trading.exchanges.types.future_exchange import (
    FutureExchange,
)
from octobot_trading.exchanges.types import websocket_exchange
from octobot_trading.exchanges.types.websocket_exchange import (
    WebSocketExchange,
)

__all__ = [
    "FutureExchange",
    "WebSocketExchange",
    "MarginExchange",
    "SpotExchange",
]
