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

from octobot_channels.constants import CHANNEL_WILDCARD

import octobot_trading.channels as channels


class FundingProducer(channels.ExchangeChannelProducer):
    async def push(self, symbol, funding_rate, next_funding_time, timestamp):
        await self.perform(symbol, funding_rate, next_funding_time, timestamp)

    async def perform(self, symbol, funding_rate, next_funding_time, timestamp):
        try:
            if self.channel.get_filtered_consumers(
                    symbol=CHANNEL_WILDCARD) or self.channel.get_filtered_consumers(symbol=symbol):
                await self.channel.exchange_manager.get_symbol_data(symbol) \
                    .handle_funding_update(funding_rate=funding_rate,
                                           next_funding_time=next_funding_time,
                                           timestamp=timestamp)
                await self.send(cryptocurrency=self.channel.exchange_manager.exchange.
                                get_pair_cryptocurrency(symbol),
                                symbol=symbol,
                                funding_rate=funding_rate,
                                next_funding_time=next_funding_time,
                                timestamp=timestamp)
        except CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.exception(e, True, f"Exception when triggering update: {e}")

    async def send(self, cryptocurrency, symbol, funding_rate, next_funding_time, timestamp):
        for consumer in self.channel.get_filtered_consumers(symbol=symbol):
            await consumer.queue.put({
                "exchange": self.channel.exchange_manager.exchange_name,
                "exchange_id": self.channel.exchange_manager.id,
                "cryptocurrency": cryptocurrency,
                "symbol": symbol,
                "funding_rate": funding_rate,
                "next_funding_time": next_funding_time,
                "timestamp": timestamp
            })


class FundingChannel(channels.ExchangeChannel):
    PRODUCER_CLASS = FundingProducer
    CONSUMER_CLASS = channels.ExchangeChannelConsumer
