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

from octobot_channels import CHANNEL_WILDCARD
from octobot_channels.producer import Producer
from octobot_commons.logging.logging_util import get_logger

from octobot_trading.channels.exchange_channel import ExchangeChannel, ExchangeChannelProducer
from octobot_trading.enums import ExchangeConstantsOrderColumns, ExchangeConstantsPositionColumns


class PositionsProducer(ExchangeChannelProducer):
    def __init__(self, channel):
        self.logger = get_logger(self.__class__.__name__)
        super().__init__(channel)
        self.channel = channel

    async def push(self, positions, is_from_bot=True):
        await self.perform(positions, is_from_bot=is_from_bot)

    async def perform(self, positions, is_from_bot=True):
        try:
            for position in positions:
                if position:
                    symbol: str = self.channel.exchange_manager.get_exchange_symbol(
                        position[ExchangeConstantsPositionColumns.SYMBOL.value])
                    if CHANNEL_WILDCARD in self.channel.consumers or symbol in self.channel.consumers:
                        position_id: str = position[ExchangeConstantsOrderColumns.ID.value]

                        changed, is_closed, is_updated = await self.channel.exchange_manager.exchange_personal_data \
                            .handle_position_update(symbol, position_id, position, should_notify=False)

                        if changed:
                            await self.send_with_wildcard(symbol=symbol,
                                                          position=position,
                                                          is_closed=is_closed,
                                                          is_updated=is_updated,
                                                          is_from_bot=is_from_bot)
        except CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.error(f"exception when triggering update: {e}")
            self.logger.exception(e)

    async def send(self, symbol, position, is_closed=False, is_updated=False, is_from_bot=True, is_wildcard=False):
        for consumer in self.channel.get_consumers(symbol=CHANNEL_WILDCARD if is_wildcard else symbol):
            await consumer.queue.put({
                "exchange": self.channel.exchange_manager.exchange.name,
                "symbol": symbol,
                "position": position,
                "is_closed": is_closed,
                "is_updated": is_updated,
                "is_from_bot": is_from_bot
            })


class PositionsChannel(ExchangeChannel):
    PRODUCER_CLASS = PositionsProducer
