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

from octobot_trading.channels.exchange_channel import get_chan
from octobot_trading.constants import RECENT_TRADES_CHANNEL
from octobot_trading.producers.orders_updater import OrdersUpdater


class OrdersUpdaterSimulator(OrdersUpdater):
    async def start(self):
        await get_chan(RECENT_TRADES_CHANNEL, self.channel.exchange_manager.id) \
            .new_consumer(self.ignore_recent_trades_update)

    async def ignore_recent_trades_update(self, exchange: str, exchange_id: str,
                                          cryptocurrency: str, symbol: str, recent_trades: list):
        """
        Used to subscribe at least one recent trades consumer during backtesting
        """
