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
import octobot_trading.exchange_channel as exchanges_channel
import octobot_trading.constants as constants
import octobot_trading.exchange_data.prices.channel.price as prices_channel
import octobot_trading.exchange_data.prices.prices_manager as prices_manager
import octobot_trading.enums as enums


class MarkPriceUpdater(prices_channel.MarkPriceProducer):
    CHANNEL_NAME = constants.MARK_PRICE_CHANNEL

    MARK_PRICE_REFRESH_TIME = 7

    def __init__(self, channel):
        super().__init__(channel)
        self.recent_trades_consumer = None
        self.ticker_consumer = None
        self.refresh_time = MarkPriceUpdater.MARK_PRICE_REFRESH_TIME

    async def start(self):
        refresh_threshold = self.channel.exchange_manager.get_rest_pairs_refresh_threshold()
        if refresh_threshold is enums.RestExchangePairsRefreshMaxThresholds.MEDIUM:
            self.refresh_time = 12
        elif refresh_threshold is enums.RestExchangePairsRefreshMaxThresholds.SLOW:
            self.refresh_time = 17
        if self.channel.is_paused:
            await self.pause()
        else:
            if not self.channel.exchange_manager.is_future:
                await self.subscribe()
            elif self._should_run():
                await self.start_fetching()

    async def subscribe(self):
        self.recent_trades_consumer = await exchanges_channel.get_chan(constants.RECENT_TRADES_CHANNEL,
                                                                       self.channel.exchange_manager.id) \
            .new_consumer(self.handle_recent_trades_update)
        self.ticker_consumer = await exchanges_channel.get_chan(constants.TICKER_CHANNEL,
                                                                self.channel.exchange_manager.id) \
            .new_consumer(self.handle_ticker_update)

    async def unsubscribe(self):
        if self.recent_trades_consumer:
            await exchanges_channel.get_chan(constants.RECENT_TRADES_CHANNEL, self.channel.exchange_manager.id) \
                .remove_consumer(self.recent_trades_consumer)
        if self.ticker_consumer:
            await exchanges_channel.get_chan(constants.TICKER_CHANNEL, self.channel.exchange_manager.id) \
                .remove_consumer(self.ticker_consumer)

    async def resume(self) -> None:
        await super().resume()
        if not self.is_running:
            await self.run()

    async def pause(self) -> None:
        await super().pause()
        if not self.channel.exchange_manager.is_future:
            await self.unsubscribe()

    async def handle_recent_trades_update(self, exchange: str, exchange_id: str,
                                          cryptocurrency: str, symbol: str, recent_trades: list):
        """
        Recent trades channel consumer callback
        """
        try:
            mark_price = prices_manager.calculate_mark_price_from_recent_trade_prices(
                [float(last_price[enums.ExchangeConstantsOrderColumns.PRICE.value])
                 for last_price in recent_trades])

            await self.push(symbol, mark_price, mark_price_source=enums.MarkPriceSources.RECENT_TRADE_AVERAGE.value)
        except Exception as e:
            self.logger.exception(e, True, f"Fail to handle recent trades update : {e}")

    async def handle_ticker_update(self, exchange: str, exchange_id: str,
                                   cryptocurrency: str, symbol: str, ticker: dict):
        """
        Ticker channel consumer callback
        """
        try:
            await self.push(symbol, ticker[enums.ExchangeConstantsTickersColumns.CLOSE.value],
                            mark_price_source=enums.MarkPriceSources.TICKER_CLOSE_PRICE.value)
        except Exception as e:
            self.logger.exception(e, True, f"Fail to handle ticker update : {e}")

    async def start_fetching(self):
        """
        Mark price updater from exchange data
        """
        while not self.should_stop and not self.channel.is_paused:
            try:
                for pair in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
                    await self.fetch_market_price(pair)
            except (errors.NotSupported, NotImplementedError):
                self.logger.warning(f"{self.channel.exchange_manager.exchange_name} is not supporting updates")
                await self.pause()
            finally:
                await asyncio.sleep(self.refresh_time)

    async def fetch_market_price(self, symbol: str):
        try:
            if self.channel.exchange_manager.exchange.FUNDING_WITH_MARK_PRICE:
                mark_price, funding_rate = await self.channel.exchange_manager.exchange. \
                    get_mark_price_and_funding(symbol)
                await self.push_funding_rate(symbol, funding_rate)
            else:
                mark_price = await self.channel.exchange_manager.exchange.get_mark_price(symbol)

            if mark_price:
                await self.push(symbol, mark_price[enums.ExchangeConstantsMarkPriceColumns.MARK_PRICE.value])
        except (errors.NotSupported, NotImplementedError) as ne:
            raise ne
        except Exception as e:
            self.logger.exception(e, True, f"Fail to update funding rate : {e}")
        return None

    async def push_funding_rate(self, symbol, funding_rate):
        if funding_rate:
            await exchanges_channel.get_chan(constants.FUNDING_CHANNEL,
                                             self.channel.exchange_manager.id).get_internal_producer(). \
                push(symbol=symbol,
                     funding_rate=funding_rate[enums.ExchangeConstantsFundingColumns.FUNDING_RATE.value],
                     next_funding_time=funding_rate[enums.ExchangeConstantsFundingColumns.NEXT_FUNDING_TIME.value],
                     timestamp=funding_rate[enums.ExchangeConstantsFundingColumns.LAST_FUNDING_TIME.value])

    def _should_run(self) -> bool:
        return self.channel.exchange_manager.exchange.FUNDING_WITH_MARK_PRICE and \
               not self.channel.exchange_manager.exchange.MARK_PRICE_IN_TICKER
