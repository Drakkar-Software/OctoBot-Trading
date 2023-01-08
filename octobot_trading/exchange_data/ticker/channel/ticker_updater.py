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
import asyncio

import octobot_trading.errors as errors
import octobot_trading.constants as constants
import octobot_trading.exchange_data.ticker.channel.ticker as ticker_channel
import octobot_trading.enums as enums


class TickerUpdater(ticker_channel.TickerProducer):
    CHANNEL_NAME = constants.TICKER_CHANNEL
    TICKER_REFRESH_TIME = 64
    TICKER_FUTURE_REFRESH_TIME = 14
    TICKER_REFRESH_DELAY_THRESHOLD = 10

    def __init__(self, channel):
        super().__init__(channel)
        self._added_pairs = []
        self.is_fetching_future_data = False
        self.refresh_time = self.TICKER_REFRESH_TIME

    async def start(self):
        if self._should_use_future():
            self.is_fetching_future_data = True
            self.refresh_time = self.TICKER_FUTURE_REFRESH_TIME
        if self.channel.is_paused:
            await self.pause()
        else:
            # initialize ticker
            await asyncio.gather(*[self._fetch_ticker(pair)
                                   for pair in self._get_pairs_to_update()])
            await asyncio.sleep(self.refresh_time)
            await self.start_update_loop()

    async def start_update_loop(self):
        while not self.should_stop and not self.channel.is_paused:
            try:
                for pair in self._get_pairs_to_update():
                    await self._fetch_ticker(pair)

                await asyncio.sleep(self.refresh_time)
            except errors.NotSupported:
                self.logger.warning(f"{self.channel.exchange_manager.exchange_name} is not supporting updates")
                await self.pause()
            except Exception as e:
                self.logger.exception(e, True, f"Fail to update ticker : {e}")

    async def _fetch_ticker(self, pair):
        try:
            ticker: dict = await self.channel.exchange_manager.exchange.get_price_ticker(pair)
            if self._is_valid(ticker):
                await self.push(pair, ticker)
            else:
                self.logger.debug(f"Ignored incomplete ticker: {ticker}")
        except errors.FailedRequest as e:
            self.logger.warning(str(e))
            # avoid spamming on disconnected situation
            await asyncio.sleep(constants.DEFAULT_FAILED_REQUEST_RETRY_TIME)

    @staticmethod
    def _is_valid(ticker):
        try:
            # at least require close, volume and timestamp
            return ticker and \
                   all(ticker[field] is not None
                       for field in (
                           enums.ExchangeConstantsTickersColumns.CLOSE.value,
                           enums.ExchangeConstantsTickersColumns.BASE_VOLUME.value,
                           enums.ExchangeConstantsTickersColumns.TIMESTAMP.value
                       ))
        except KeyError:
            return False

    def _get_pairs_to_update(self):
        return self.channel.exchange_manager.exchange_config.traded_symbol_pairs + self._added_pairs


    """
    Future data management
    """

    def _should_use_future(self):
        return self.channel.exchange_manager.is_future and \
               (
                       self.channel.exchange_manager.exchange.FUNDING_IN_TICKER
                       or self.channel.exchange_manager.exchange.MARK_PRICE_IN_TICKER
               )

    async def modify(self, added_pairs=None, removed_pairs=None):
        if added_pairs:
            to_add_pairs = [pair
                            for pair in added_pairs
                            if pair not in self._get_pairs_to_update()]
            if to_add_pairs:
                self._added_pairs += to_add_pairs
                self.logger.info(f"Added pairs : {to_add_pairs}")
                self._update_refresh_time()

        if removed_pairs:
            self._added_pairs -= removed_pairs
            self.logger.info(f"Removed pairs : {removed_pairs}")
            self._update_refresh_time()

    def _update_refresh_time(self):
        if self.is_fetching_future_data:
            # do not change ticker update rate on futures
            return
        pairs_to_update_count = len(self._get_pairs_to_update())
        delay_multiplier = pairs_to_update_count // self.TICKER_REFRESH_DELAY_THRESHOLD + 1
        # there can be many ticker requests when a large number of currency is in a
        # portfolio, in this case, limit those requests
        self.refresh_time = self.TICKER_REFRESH_TIME * delay_multiplier

    async def resume(self) -> None:
        await super().resume()
        if not self.is_running:
            await self.run()
