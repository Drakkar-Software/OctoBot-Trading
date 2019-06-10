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
import asyncio

from octobot_trading.channels.recent_trade import RecentTradeProducer


class RecentTradeUpdater(RecentTradeProducer):
    RECENT_TRADE_REFRESH_TIME = 5
    RECENT_TRADE_LIMIT = 10

    def __init__(self, channel):
        super().__init__(channel)
        self.should_stop = False
        self.channel = channel

    async def start(self):
        await self.initialize()
        while not self.should_stop:
            try:
                for pair in self.channel.exchange_manager.traded_pairs:
                    await self.push(pair,
                                    await self.channel.exchange_manager.exchange.get_recent_trades(pair,
                                                                                                   limit=self.RECENT_TRADE_LIMIT))
                await asyncio.sleep(self.RECENT_TRADE_REFRESH_TIME)
            except Exception as e:
                self.logger.exception(f"Fail to update recent trades : {e}")

    async def initialize(self):
        try:
            for pair in self.channel.exchange_manager.traded_pairs:
                await self.push(pair,
                                await self.channel.exchange_manager.exchange.get_recent_trades(pair))
            await asyncio.sleep(self.RECENT_TRADE_REFRESH_TIME)
        except Exception as e:
            self.logger.exception(f"Fail to initialize recent trades : {e}")
