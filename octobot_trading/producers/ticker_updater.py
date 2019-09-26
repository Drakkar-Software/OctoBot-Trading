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

from octobot_trading.channels.ticker import TickerProducer


class TickerUpdater(TickerProducer):
    TICKER_REFRESH_TIME = 64

    def __init__(self, channel):
        super().__init__(channel)
        self._pairs_to_update = []

    async def start(self):
        self._pairs_to_update = self.channel.exchange_manager.traded_pairs

        while not self.should_stop:
            try:
                for pair in self._pairs_to_update:
                    ticker: dict = await self.channel.exchange_manager.exchange.get_price_ticker(pair)

                    if ticker:
                        await self.push(pair, ticker)

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

    async def modify(self, added_pairs=None, removed_pairs=None):
        if added_pairs:
            self._pairs_to_update += added_pairs
            self.logger.info(f"Added pairs : {added_pairs}")

        if removed_pairs:
            self._pairs_to_update -= removed_pairs
            self.logger.info(f"Removed pairs : {removed_pairs}")
