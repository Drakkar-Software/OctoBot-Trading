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
from octobot_channels.producer import Producer
from octobot_commons.logging.logging_util import get_logger

from octobot_trading.channels.exchange_channel import ExchangeChannel, ExchangeChannelProducer, ExchangeChannelConsumer
from octobot_trading.enums import ExchangeConstantsOrderColumns


class OrdersProducer(ExchangeChannelProducer):
    async def push(self, orders, is_closed=False, is_from_bot=True):
        await self.perform(orders, is_closed=is_closed, is_from_bot=is_from_bot)

    async def perform(self, orders, is_closed=False, is_from_bot=True):
        try:
            for order in orders:
                symbol: str = order[ExchangeConstantsOrderColumns.SYMBOL.value]
                if self.channel.get_filtered_consumers(symbol=CHANNEL_WILDCARD) or self.channel.get_filtered_consumers(
                        symbol=symbol):
                    order_id: str = order[ExchangeConstantsOrderColumns.ID.value]
                    is_updated: bool = False
                    if is_closed:
                        changed = await self.channel.exchange_manager.exchange_personal_data.handle_closed_order_update(
                            symbol,
                            order_id,
                            order,
                            should_notify=False)
                    else:
                        changed, is_updated = await self.channel.exchange_manager.exchange_personal_data.handle_order_update(
                            symbol,
                            order_id,
                            order,
                            should_notify=False)

                    if changed:
                        await self.send(symbol=symbol, order=order,
                                        is_from_bot=is_from_bot,
                                        is_closed=is_closed,
                                        is_updated=is_updated)
        except CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.exception(e, True, f"Exception when triggering update: {e}")

    async def send(self, symbol, order, is_from_bot=True, is_closed=False, is_updated=False):
        for consumer in self.channel.get_filtered_consumers(symbol=symbol):
            await consumer.queue.put({
                "exchange": self.channel.exchange_manager.exchange_name,
                "exchange_id": self.channel.exchange_manager.id,
                "symbol": symbol,
                "order": order,
                "is_closed": is_closed,
                "is_updated": is_updated,
                "is_from_bot": is_from_bot
            })


class OrdersChannel(ExchangeChannel):
    PRODUCER_CLASS = OrdersProducer
    CONSUMER_CLASS = ExchangeChannelConsumer
