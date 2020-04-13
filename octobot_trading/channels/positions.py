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
from octobot_trading.channels.exchange_channel import ExchangeChannel, ExchangeChannelProducer, ExchangeChannelConsumer
from octobot_trading.enums import ExchangeConstantsOrderColumns, ExchangeConstantsPositionColumns


class PositionsProducer(ExchangeChannelProducer):
    async def push(self, positions, is_closed=False, is_liquidated=False, is_from_bot=True):
        await self.perform(positions, is_closed=is_closed, is_liquidated=is_liquidated, is_from_bot=is_from_bot)

    async def perform(self, positions, is_closed=False, is_liquidated=False, is_from_bot=True):
        try:
            for position in positions:
                symbol: str = self.channel.exchange_manager.get_exchange_symbol(
                    position[ExchangeConstantsPositionColumns.SYMBOL.value])
                if self.channel.get_filtered_consumers(
                        symbol=CHANNEL_WILDCARD) or self.channel.get_filtered_consumers(symbol=symbol):
                    position_id: str = position[ExchangeConstantsPositionColumns.ID.value]

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
                                        is_closed=is_closed,
                                        is_updated=changed,
                                        is_liquidated=is_liquidated,
                                        is_from_bot=is_from_bot)
        except CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.exception(e, True, f"Exception when triggering update: {e}")

    async def send(self, cryptocurrency, symbol, position, is_closed=False, is_updated=False, is_liquidated=False, is_from_bot=True):
        for consumer in self.channel.get_filtered_consumers(symbol=symbol):
            await consumer.queue.put({
                "exchange": self.channel.exchange_manager.exchange_name,
                "exchange_id": self.channel.exchange_manager.id,
                "cryptocurrency": cryptocurrency,
                "symbol": symbol,
                "position": position,
                "is_closed": is_closed,
                "is_updated": is_updated,
                "is_liquidated": is_liquidated,
                "is_from_bot": is_from_bot
            })


class PositionsChannel(ExchangeChannel):
    PRODUCER_CLASS = PositionsProducer
    CONSUMER_CLASS = ExchangeChannelConsumer
