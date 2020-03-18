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

from ccxt.base.errors import NotSupported

from octobot_trading.channels.exchange_channel import get_chan
from octobot_trading.constants import TICKER_CHANNEL, FUNDING_CHANNEL, MARK_PRICE_CHANNEL
from octobot_trading.channels.ticker import TickerProducer
from octobot_trading.enums import ExchangeConstantsFundingColumns, ExchangeConstantsMarkPriceColumns


class TickerUpdater(TickerProducer):
    CHANNEL_NAME = TICKER_CHANNEL
    TICKER_REFRESH_TIME = 64
    TICKER_FUTURE_REFRESH_TIME = 14

    def __init__(self, channel):
        super().__init__(channel)
        self._added_pairs = []
        self.is_fetching_future_data = False

    async def start(self):
        if self._should_use_future():
            self.is_fetching_future_data = True
            self.TICKER_REFRESH_TIME = self.TICKER_FUTURE_REFRESH_TIME

        while not self.should_stop and not self.channel.is_paused:
            try:
                for pair in self._get_pairs_to_update():
                    ticker: dict = await self.channel.exchange_manager.exchange.get_price_ticker(pair)

                    if ticker:
                        await self.push(pair, ticker)

                        if self.channel.exchange_manager.is_future:
                            await self.parse_future_data(pair, ticker)

                await asyncio.sleep(self.TICKER_REFRESH_TIME)
            except NotSupported:
                self.logger.warning(f"{self.channel.exchange_manager.exchange_name} is not supporting updates")
                await self.pause()
            except Exception as e:
                self.logger.exception(e, True, f"Fail to update ticker : {e}")

    def _cleanup_ticker_dict(self, ticker):
        try:
            ticker.pop("info")
            ticker.pop("symbol")
            ticker.pop("datetime")
        except KeyError as e:
            self.logger.error(f"Fail to cleanup ticker dict ({e})")
        return ticker

    def _get_pairs_to_update(self):
        return self.channel.exchange_manager.exchange_config.traded_symbol_pairs + self._added_pairs

    """
    Future data management
    """

    def _should_use_future(self):
        return self.channel.exchange_manager.is_future and \
               (self.channel.exchange_manager.exchange.FUNDING_IN_TICKER
                or self.channel.exchange_manager.exchange.MARK_PRICE_IN_TICKER)

    async def parse_future_data(self, symbol: str, ticker: dict):
        if self.channel.exchange_manager.exchange.MARK_PRICE_IN_TICKER:
            await self.extract_mark_price(symbol, ticker)

        if self.channel.exchange_manager.exchange.FUNDING_IN_TICKER:
            await self.extract_funding_rate(symbol, ticker)

    async def extract_mark_price(self, symbol: str, ticker: dict):
        try:
            ticker = self.channel.exchange_manager.exchange.cleanup_mark_price_dict(ticker, from_ticker=True)
            await get_chan(MARK_PRICE_CHANNEL, self.channel.exchange_manager.id).get_internal_producer(). \
                push(symbol=symbol, mark_price=ticker[ExchangeConstantsMarkPriceColumns.MARK_PRICE.value])
        except Exception as e:
            self.logger.exception(e, True, f"Fail to update mark price from ticker : {e}")

    async def extract_funding_rate(self, symbol: str, ticker: dict):
        try:
            ticker = self.channel.exchange_manager.exchange.cleanup_funding_dict(ticker, from_ticker=True)
            await get_chan(FUNDING_CHANNEL, self.channel.exchange_manager.id).get_internal_producer(). \
                push(symbol=symbol,
                     funding_rate=ticker[ExchangeConstantsFundingColumns.FUNDING_RATE.value],
                     next_funding_time=ticker[ExchangeConstantsFundingColumns.NEXT_FUNDING_TIME.value],
                     timestamp=ticker[ExchangeConstantsFundingColumns.TIMESTAMP.value])
        except Exception as e:
            self.logger.exception(e, True, f"Fail to update funding rate from ticker : {e}")

    async def modify(self, added_pairs=None, removed_pairs=None):
        if added_pairs:
            to_add_pairs = [pair
                            for pair in added_pairs
                            if pair not in self._get_pairs_to_update()]
            if to_add_pairs:
                self._added_pairs += to_add_pairs
                self.logger.info(f"Added pairs : {to_add_pairs}")

        if removed_pairs:
            self._added_pairs -= removed_pairs
            self.logger.info(f"Removed pairs : {removed_pairs}")

    # async def config_callback(self, exchange, cryptocurrency, symbols, time_frames):
    #     if symbols:
    #         await self.modify(added_pairs=symbols)

    async def resume(self) -> None:
        await super().resume()
        if not self.is_running:
            await self.run()
