# pylint: disable=E0611
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
import copy

from ccxt.base.errors import InsufficientFunds

from octobot_commons.logging.logging_util import get_logger
from octobot_trading.constants import RECENT_TRADES_CHANNEL, ORDERS_CHANNEL
from octobot_trading.channels.exchange_channel import get_chan
from octobot_trading.data.order import Order
from octobot_trading.enums import OrderStatus
from octobot_trading.producers import MissingOrderException
from octobot_trading.producers.orders_updater import OpenOrdersUpdater, CloseOrdersUpdater


class OpenOrdersUpdaterSimulator(OpenOrdersUpdater):
    async def start(self):
        pass


class CloseOrdersUpdaterSimulator(CloseOrdersUpdater):
    async def start(self):
        pass
