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

import async_channel.constants as constants

import octobot_trading.exchange_channel as exchanges_channel


class TickerProducer(exchanges_channel.ExchangeChannelProducer):
    async def push(self, symbol, ticker):
        await self.perform(symbol, ticker)

    async def perform(self, symbol, ticker):
        try:
            if self.channel.get_filtered_consumers(symbol=constants.CHANNEL_WILDCARD) or \
                    self.channel.get_filtered_consumers(symbol=symbol):  #
                if ticker:  # and price_ticker_is_initialized
                    self.channel.exchange_manager.get_symbol_data(symbol).handle_ticker_update(ticker)
                    await self.send(cryptocurrency=self.channel.exchange_manager.exchange.
                                    get_pair_cryptocurrency(symbol),
                                    symbol=symbol,
                                    ticker=ticker)
        except asyncio.CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.exception(e, True, f"Exception when triggering update: {e}")

    async def send(self, cryptocurrency, symbol, ticker):
        for consumer in self.channel.get_filtered_consumers(symbol=symbol):
            await consumer.queue.put({
                "exchange": self.channel.exchange_manager.exchange_name,
                "exchange_id": self.channel.exchange_manager.id,
                "cryptocurrency": cryptocurrency,
                "symbol": symbol,
                "ticker": ticker
            })


class TickerChannel(exchanges_channel.ExchangeChannel):
    PRODUCER_CLASS = TickerProducer
    CONSUMER_CLASS = exchanges_channel.ExchangeChannelConsumer


class MiniTickerProducer(exchanges_channel.ExchangeChannelProducer):
    async def push(self, symbol, mini_ticker):
        await self.perform(symbol, mini_ticker)

    async def perform(self, symbol, mini_ticker):
        try:
            if self.channel.get_filtered_consumers(symbol=constants.CHANNEL_WILDCARD) or \
                    self.channel.get_filtered_consumers(symbol=symbol):
                if mini_ticker:
                    self.channel.exchange_manager.get_symbol_data(symbol).handle_mini_ticker_update(mini_ticker)
                    await self.send(cryptocurrency=self.channel.exchange_manager.exchange.
                                    get_pair_cryptocurrency(symbol),
                                    symbol=symbol,
                                    mini_ticker=mini_ticker)
        except asyncio.CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.exception(e, True, f"Exception when triggering update: {e}")

    async def send(self, cryptocurrency, symbol, mini_ticker):
        for consumer in self.channel.get_filtered_consumers(symbol=symbol):
            await consumer.queue.put({
                "exchange": self.channel.exchange_manager.exchange_name,
                "exchange_id": self.channel.exchange_manager.id,
                "cryptocurrency": cryptocurrency,
                "symbol": symbol,
                "mini_ticker": mini_ticker
            })


class MiniTickerChannel(exchanges_channel.ExchangeChannel):
    PRODUCER_CLASS = MiniTickerProducer
    CONSUMER_CLASS = exchanges_channel.ExchangeChannelConsumer
