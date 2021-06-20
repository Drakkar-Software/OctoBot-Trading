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

import async_channel.constants as channel_constants

import octobot_trading.exchange_channel as exchanges_channel
import octobot_trading.enums as enums


class PositionsProducer(exchanges_channel.ExchangeChannelProducer):
    async def push(self, positions, is_liquidated=False):
        await self.perform(positions, is_liquidated=is_liquidated)

    async def perform(self, positions, is_liquidated=False):
        try:
            for position in positions:
                if not position:
                    continue
                symbol: str = position[enums.ExchangeConstantsPositionColumns.SYMBOL.value]
                if self.channel.get_filtered_consumers(symbol=channel_constants.CHANNEL_WILDCARD) or \
                        self.channel.get_filtered_consumers(symbol=symbol):
                    position_id: str = position[enums.ExchangeConstantsPositionColumns.ID.value]

                    changed = await self.channel.exchange_manager.exchange_personal_data. \
                        handle_position_update(symbol=symbol,
                                               position_id=position_id,
                                               position=position,
                                               should_notify=False)

                    if changed:
                        await self.send(cryptocurrency=self.channel.exchange_manager.exchange.
                                        get_pair_cryptocurrency(symbol),
                                        symbol=symbol,
                                        position=position,
                                        is_updated=changed,
                                        is_liquidated=is_liquidated)
        except asyncio.CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.exception(e, True, f"Exception when triggering update: {e}")

    async def send(self, cryptocurrency, symbol, position, is_updated=False, is_liquidated=False):
        for consumer in self.channel.get_filtered_consumers(symbol=symbol):
            await consumer.queue.put({
                "exchange": self.channel.exchange_manager.exchange_name,
                "exchange_id": self.channel.exchange_manager.id,
                "cryptocurrency": cryptocurrency,
                "symbol": symbol,
                "position": position,
                "is_updated": is_updated,
                "is_liquidated": is_liquidated
            })


class PositionsChannel(exchanges_channel.ExchangeChannel):
    PRODUCER_CLASS = PositionsProducer
    CONSUMER_CLASS = exchanges_channel.ExchangeChannelConsumer
