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
from octobot_trading.enums import ExchangeConstantsOrderColumns


class TradesProducer(ExchangeChannelProducer):
    async def push(self, trades, old_trade=False):
        await self.perform(trades, old_trade=old_trade)

    async def perform(self, trades, old_trade=False):
        try:
            for trade in trades:
                symbol: str = self.channel.exchange_manager.get_exchange_symbol(
                    trade[ExchangeConstantsOrderColumns.SYMBOL.value])
                if self.channel.get_filtered_consumers(symbol=CHANNEL_WILDCARD) or \
                        self.channel.get_filtered_consumers(symbol=symbol):
                    trade_id: str = trade[ExchangeConstantsOrderColumns.ID.value]

                    added: bool = await self.channel.exchange_manager.exchange_personal_data.handle_trade_update(
                        symbol,
                        trade_id,
                        trade,
                        should_notify=False)

                    if added:
                        await self.send(cryptocurrency=self.channel.exchange_manager.exchange.
                                        get_pair_cryptocurrency(symbol),
                                        symbol=symbol,
                                        trade=trade,
                                        old_trade=old_trade)
        except CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.exception(e, True, f"Exception when triggering update: {e}")

    async def send(self, cryptocurrency, symbol, trade, old_trade=False):
        for consumer in self.channel.get_filtered_consumers(symbol=symbol):
            await consumer.queue.put({
                "exchange": self.channel.exchange_manager.exchange_name,
                "exchange_id": self.channel.exchange_manager.id,
                "cryptocurrency": cryptocurrency,
                "symbol": symbol,
                "trade": trade,
                "old_trade": old_trade
            })


class TradesChannel(ExchangeChannel):
    PRODUCER_CLASS = TradesProducer
    CONSUMER_CLASS = ExchangeChannelConsumer
