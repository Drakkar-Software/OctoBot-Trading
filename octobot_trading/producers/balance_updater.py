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

from ccxt.base.errors import NotSupported

from octobot_commons.logging.logging_util import get_logger
from octobot_trading.constants import BALANCE_CHANNEL, TICKER_CHANNEL
from octobot_trading.channels.balance import BalanceProducer, BalanceProfitabilityProducer
from octobot_trading.channels.exchange_channel import get_chan


class BalanceUpdater(BalanceProducer):
    BALANCE_REFRESH_TIME = 666
    CHANNEL_NAME = BALANCE_CHANNEL

    async def start(self):
        while not self.should_stop and not self.channel.is_paused:
            try:
                await self.push((await self.channel.exchange_manager.exchange.get_balance()))
                await asyncio.sleep(self.BALANCE_REFRESH_TIME)
            except NotSupported:
                self.logger.warning(f"{self.channel.exchange_manager.exchange.name} is not supporting updates")
                await self.pause()
            except Exception as e:
                self.logger.error(f"Failed to update balance : {e}")

    async def resume(self) -> None:
        await super().resume()
        if not self.is_running:
            await self.run()


class BalanceProfitabilityUpdater(BalanceProfitabilityProducer):
    CHANNEL_NAME = BALANCE_CHANNEL

    def __init__(self, channel):
        super().__init__(channel)
        self.logger = get_logger(self.__class__.__name__)
        self.exchange_personal_data = self.channel.exchange_manager.exchange_personal_data

    async def start(self):
        await get_chan(BALANCE_CHANNEL, self.channel.exchange.name).new_consumer(
            self.handle_balance_update)
        await get_chan(TICKER_CHANNEL, self.channel.exchange.name).new_consumer(
            self.handle_ticker_update)

    """
    Balance channel consumer callback
    """

    async def handle_balance_update(self, exchange: str, exchange_id: str, balance: dict):
        try:
            await self.exchange_personal_data.handle_portfolio_profitability_update(balance=balance, ticker=None, symbol=None)
        except Exception as e:
            self.logger.exception(f"Fail to handle balance update : {e}")

    """
    Ticker channel consumer callback
    """

    async def handle_ticker_update(self, exchange: str, exchange_id: str, symbol: str, ticker: dict):
        try:
            await self.exchange_personal_data.handle_portfolio_profitability_update(symbol=symbol, ticker=ticker, balance=None)
        except Exception as e:
            self.logger.exception(f"Fail to handle ticker update : {e}")
