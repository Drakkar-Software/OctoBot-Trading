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
from asyncio import CancelledError, Queue

from octobot_channels import CHANNEL_WILDCARD, CONSUMER_CALLBACK_TYPE
from octobot_trading.channels.exchange_channel import ExchangeChannel
from octobot_channels.consumer import Consumer
from octobot_channels.producer import Producer


class RecentTradeProducer(Producer):
    async def push(self, symbol, recent_trades, forced=False):
        await self.perform(symbol, recent_trades, forced=forced)

    async def perform(self, symbol, recent_trades, forced=False):
        try:
            if CHANNEL_WILDCARD in self.channel.consumers or symbol in self.channel.consumers:  # and symbol_data.recent_trades_are_initialized()
                self.channel.exchange_manager.get_symbol_data(symbol).handle_recent_trade_update(recent_trades)
                self.channel.will_send()
                await self.send(symbol, recent_trades, False)
                await self.send(symbol, recent_trades, True)
                self.channel.has_send()
        except CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.error(f"exception when triggering update: {e}")
            self.logger.exception(e)

    async def send(self, symbol, recent_trades, is_wildcard=False):
        for consumer in self.channel.get_consumers(symbol=CHANNEL_WILDCARD if is_wildcard else symbol):
            await consumer.queue.put({
                "symbol": symbol,
                "recent_trades": recent_trades
            })


class RecentTradeConsumer(Consumer):
    def __init__(self, callback: CONSUMER_CALLBACK_TYPE, size=0, filter_size=0):  # TODO REMOVE
        super().__init__(callback)
        self.filter_size = 0
        self.should_stop = False
        self.queue = Queue()
        self.callback = callback

    async def consume(self):
        while not self.should_stop:
            try:
                data = await self.queue.get()
                await self.callback(symbol=data["symbol"], recent_trades=data["recent_trades"])
            except Exception as e:
                self.logger.exception(f"Exception when calling callback : {e}")


class RecentTradeChannel(ExchangeChannel):
    FILTER_SIZE = 10

    def new_consumer(self, callback: CONSUMER_CALLBACK_TYPE,
                     size: int = 0,
                     symbol: str = CHANNEL_WILDCARD,
                     filter_size: bool = False):
        self._add_new_consumer_and_run(RecentTradeConsumer(callback, size=size, filter_size=filter_size), symbol=symbol)
