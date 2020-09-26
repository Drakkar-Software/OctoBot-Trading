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
from octobot_trading.trades import trade
from octobot_trading.trades import trade_factory
from octobot_trading.trades import trades_manager

from octobot_trading.trades.trade import (Trade,)
from octobot_trading.trades.trade_factory import (create_trade_from_order,
                                                  create_trade_instance,
                                                  create_trade_instance_from_raw,)
from octobot_trading.trades.trades_manager import (TradesManager,)

__all__ = ['Trade', 'TradesManager', 'create_trade_from_order',
           'create_trade_instance', 'create_trade_instance_from_raw', 'trade',
           'trade_factory', 'trades_manager']
