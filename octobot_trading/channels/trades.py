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
from octobot_commons.logging.logging_util import get_logger

from octobot_trading.channels.exchange_channel import ExchangeChannel
from octobot_channels.consumer import Consumer
from octobot_channels.producer import Producer

from octobot_trading.enums import ExchangeConstantsOrderColumns


class TradesProducer(Producer):
    def __init__(self, channel):
        self.logger = get_logger(self.__class__.__name__)
        super().__init__(channel)

    async def push(self, trades, old_trade=False):
        await self.perform(trades, old_trade=old_trade)

    async def perform(self, trades, old_trade=False):
        try:
            for trade in trades:
                symbol: str = self.channel.exchange_manager.get_exchange_symbol(
                    trade[ExchangeConstantsOrderColumns.SYMBOL.value])
                if CHANNEL_WILDCARD in self.channel.consumers or symbol in self.channel.consumers:
                    trade_id: str = trade[ExchangeConstantsOrderColumns.ID.value]

                    added: bool = self.channel.exchange_manager.exchange_personal_data.handle_trade_update(
                        trade_id,
                        trade)

                    if added:
                        await self.send(symbol, trade, old_trade)
                        await self.send(symbol, trade, old_trade, True)
        except CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.error(f"exception when triggering update: {e}")
            self.logger.exception(e)

    async def send(self, symbol, trade, old_trade=False, is_wildcard=False):
        for consumer in self.channel.get_consumers(symbol=CHANNEL_WILDCARD if is_wildcard else symbol):
            await consumer.queue.put({
                "exchange": self.channel.exchange_manager.exchange.name,
                "symbol": symbol,
                "trade": trade,
                "old_trade": old_trade
            })


class TradesConsumer(Consumer):
    def __init__(self, callback: CONSUMER_CALLBACK_TYPE, size=0, symbol=""):   # TODO REMOVE
        super().__init__(callback)
        self.filter_size = 0
        self.symbol = symbol
        self.should_stop = False
        self.queue = Queue()
        self.callback = callback

    async def consume(self):
        while not self.should_stop:
            try:
                data = await self.queue.get()
                await self.callback(exchange=data["exchange"], symbol=data["symbol"],
                                    trade=data["trade"], old_trade=data["old_trade"])
            except Exception as e:
                self.logger.exception(f"Exception when calling callback : {e}")


class TradesChannel(ExchangeChannel):
    def new_consumer(self, callback: CONSUMER_CALLBACK_TYPE, size: int = 0, symbol: str = CHANNEL_WILDCARD):
        self._add_new_consumer_and_run(TradesConsumer(callback, size=size), symbol=symbol)
