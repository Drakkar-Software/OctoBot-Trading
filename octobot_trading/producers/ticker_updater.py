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

from octobot_trading.channels.ticker import TickerProducer


class TickerUpdater(TickerProducer):
    TICKER_REFRESH_TIME = 60

    def __init__(self, channel):
        super().__init__(channel)
        self.should_stop = False
        self.channel = channel

    async def start(self):
        while not self.should_stop:
            try:
                for pair in self.channel.exchange_manager.traded_pairs:
                    ticker: dict = await self.channel.exchange_manager.exchange.get_price_ticker(pair)
                    await self.push(pair, await self.push(pair, self._cleanup_ticker_dict(ticker)))
                await asyncio.sleep(self.TICKER_REFRESH_TIME)
            except Exception as e:
                self.logger.exception(f"Fail to update ticker : {e}")

    def _cleanup_ticker_dict(self, ticker):
        try:
            ticker.pop("info")
            ticker.pop("symbol")
            ticker.pop("datetime")
        except KeyError as e:
            self.logger.error(f"Fail to cleanup ticker dict ({e})")
        return ticker
