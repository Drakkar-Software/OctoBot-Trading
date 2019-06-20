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


class OrdersProducer(Producer):
    def __init__(self, channel):
        self.logger = get_logger(self.__class__.__name__)
        super().__init__(channel)

    async def push(self, orders, is_closed=False):
        await self.perform(orders, is_closed=is_closed)

    async def perform(self, orders, is_closed=False):
        try:
            for order in orders:
                symbol: str = order[ExchangeConstantsOrderColumns.SYMBOL.value]
                if CHANNEL_WILDCARD in self.channel.consumers or symbol in self.channel.consumers:
                    order_id: str = order[ExchangeConstantsOrderColumns.ID.value]

                    if is_closed:
                        changed: bool = self.channel.exchange_manager.exchange_personal_data.handle_closed_order_update(order_id, order)
                    else:
                        changed: bool = self.channel.exchange_manager.exchange_personal_data.handle_order_update(order_id, order)

                    if changed:
                        await self.send(symbol, order, is_closed)
                        await self.send(symbol, order, is_closed, True)
        except CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.error(f"exception when triggering update: {e}")
            self.logger.exception(e)

    async def send(self, symbol, order, is_closed=False, is_wildcard=False):
        for consumer in self.channel.get_consumers(symbol=CHANNEL_WILDCARD if is_wildcard else symbol):
            await consumer.queue.put({
                "symbol": symbol,
                "order": order,
                "is_closed": is_closed
            })


class OrdersConsumer(Consumer):
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
                await self.callback(symbol=data["symbol"], order=data["order"], is_closed=data["is_closed"])
            except Exception as e:
                self.logger.exception(f"Exception when calling callback : {e}")


class OrdersChannel(ExchangeChannel):
    def new_consumer(self, callback: CONSUMER_CALLBACK_TYPE, size: int = 0, symbol: str = CHANNEL_WILDCARD):
        self._add_new_consumer_and_run(OrdersConsumer(callback, size=size), symbol=symbol)
