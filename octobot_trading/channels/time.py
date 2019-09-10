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
from asyncio import CancelledError

from octobot_trading.channels.exchange_channel import ExchangeChannel, ExchangeChannelProducer, ExchangeChannelSupervisedConsumer


class TimeProducer(ExchangeChannelProducer):
    async def push(self, timestamp):
        await self.perform(timestamp)

    async def perform(self, timestamp):
        try:
            await self.channel.exchange_manager.exchange_global_data.handle_time_update(timestamp)
            await self.send(timestamp=timestamp)
        except CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.error(f"exception when triggering time update: {e}")
            self.logger.exception(e)

    async def send(self, timestamp):
        for consumer in self.channel.get_filtered_consumers():
            await consumer.queue.put({
                "exchange": self.channel.exchange_manager.exchange.name,
                "timestamp": timestamp
            })


class TimeConsumer(ExchangeChannelSupervisedConsumer):
    pass


class TimeChannel(ExchangeChannel):
    PRODUCER_CLASS = TimeProducer
    CONSUMER_CLASS = TimeConsumer
