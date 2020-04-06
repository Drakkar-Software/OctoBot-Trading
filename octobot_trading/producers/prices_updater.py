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

from ccxt import NotSupported

from octobot_trading.channels.exchange_channel import get_chan
from octobot_trading.channels.price import MarkPriceProducer
from octobot_trading.constants import MARK_PRICE_CHANNEL, RECENT_TRADES_CHANNEL, TICKER_CHANNEL, FUNDING_CHANNEL
from octobot_trading.data_manager.prices_manager import PricesManager
from octobot_trading.enums import ExchangeConstantsTickersColumns, ExchangeConstantsOrderColumns, \
    ExchangeConstantsFundingColumns, ExchangeConstantsMarkPriceColumns


class MarkPriceUpdater(MarkPriceProducer):
    CHANNEL_NAME = MARK_PRICE_CHANNEL

    MARK_PRICE_REFRESH_TIME = 7

    def __init__(self, channel):
        super().__init__(channel)
        self.recent_trades_consumer = None
        self.ticker_consumer = None

    async def start(self):
        if not self.channel.exchange_manager.is_future:
            await self.subscribe()
        elif self._should_run():
            await self.start_fetching()

    async def subscribe(self):
        self.recent_trades_consumer = await get_chan(RECENT_TRADES_CHANNEL, self.channel.exchange_manager.id) \
            .new_consumer(self.handle_recent_trades_update)
        self.ticker_consumer = await get_chan(TICKER_CHANNEL, self.channel.exchange_manager.id) \
            .new_consumer(self.handle_ticker_update)

    async def unsubscribe(self):
        if self.recent_trades_consumer:
            await get_chan(RECENT_TRADES_CHANNEL, self.channel.exchange_manager.id) \
                .remove_consumer(self.recent_trades_consumer)
        if self.ticker_consumer:
            await get_chan(TICKER_CHANNEL, self.channel.exchange_manager.id) \
                .remove_consumer(self.ticker_consumer)

    async def resume(self) -> None:
        await super().resume()
        if not self.is_running:
            await self.run()

    async def pause(self) -> None:
        await super().pause()
        if not self.channel.exchange_manager.is_future:
            await self.unsubscribe()

    """
    Recent trades channel consumer callback
    """

    async def handle_recent_trades_update(self, exchange: str, exchange_id: str, symbol: str, recent_trades: list):
        try:
            mark_price = PricesManager.calculate_mark_price_from_recent_trade_prices(
                [float(last_price[ExchangeConstantsOrderColumns.PRICE.value])
                 for last_price in recent_trades])

            await self.push(symbol, mark_price)
        except Exception as e:
            self.logger.exception(e, True, f"Fail to handle recent trades update : {e}")

    """
    Ticker channel consumer callback
    """

    async def handle_ticker_update(self, exchange: str, exchange_id: str, symbol: str, ticker: dict):
        try:
            await self.push(symbol, ticker[ExchangeConstantsTickersColumns.CLOSE.value])
        except Exception as e:
            self.logger.exception(e, True, f"Fail to handle ticker update : {e}")

    """
    Mark price updater from exchange data
    """

    async def start_fetching(self):
        while not self.should_stop and not self.channel.is_paused:
            try:
                for pair in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
                    await self.fetch_market_price(pair)
            except (NotSupported, NotImplementedError):
                self.logger.warning(f"{self.channel.exchange_manager.exchange_name} is not supporting updates")
                await self.pause()
            finally:
                await asyncio.sleep(self.MARK_PRICE_REFRESH_TIME)

    async def fetch_market_price(self, symbol: str):
        try:
            if self.channel.exchange_manager.exchange.FUNDING_WITH_MARK_PRICE:
                mark_price, funding_rate = await self.channel.exchange_manager.exchange. \
                    get_mark_price_and_funding(symbol)
                await self.push_funding_rate(symbol, funding_rate)
            else:
                mark_price = await self.channel.exchange_manager.exchange.get_mark_price(symbol)

            if mark_price:
                await self.push(symbol, mark_price[ExchangeConstantsMarkPriceColumns.MARK_PRICE.value])
        except (NotSupported, NotImplementedError) as ne:
            raise ne
        except Exception as e:
            self.logger.exception(e, True, f"Fail to update funding rate : {e}")
        return None

    async def push_funding_rate(self, symbol, funding_rate):
        if funding_rate:
            await get_chan(FUNDING_CHANNEL, self.channel.exchange_manager.id).get_internal_producer(). \
                push(symbol=symbol,
                     funding_rate=funding_rate[ExchangeConstantsFundingColumns.FUNDING_RATE.value],
                     next_funding_time=funding_rate[ExchangeConstantsFundingColumns.NEXT_FUNDING_TIME.value],
                     timestamp=funding_rate[ExchangeConstantsFundingColumns.LAST_FUNDING_TIME.value])

    def _should_run(self) -> bool:
        return self.channel.exchange_manager.exchange.FUNDING_WITH_MARK_PRICE and \
               not self.channel.exchange_manager.exchange.MARK_PRICE_IN_TICKER
