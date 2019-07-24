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

from octobot_commons.logging.logging_util import get_logger

from octobot_trading.channels.balance import BalanceProducer


class BalanceUpdater(BalanceProducer):
    BALANCE_REFRESH_TIME = 666

    def __init__(self, channel):
        super().__init__(channel)
        self.logger = get_logger(f"{self.__class__.__name__}")
        self.should_stop = False
        self.channel = channel

    async def start(self):
        while not self.should_stop:
            try:
                await self.push((await self.channel.exchange_manager.exchange.get_balance()))
                await asyncio.sleep(self.BALANCE_REFRESH_TIME)
            except Exception as e:
                self.logger.error(f"Failed to update balance : {e}")
