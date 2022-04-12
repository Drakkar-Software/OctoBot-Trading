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
import async_channel.enums as channel_enums
import octobot_commons.logging as logging
import octobot_commons.enums as commons_enums
import octobot_trading.signals.channel.remote_trading_signal as signals_channel
import octobot_trading.signals.trading_signal_factory as trading_signal_factory


class RemoteTradingSignalProducer(signals_channel.RemoteTradingSignalChannelProducer):
    def __init__(self, channel, authenticator, bot_id):
        super().__init__(channel)
        # the trading mode instance logger
        self.logger = logging.get_logger(self.__class__.__name__)

        # Define trading modes default consumer priority level
        self.priority_level: int = channel_enums.ChannelConsumerPriorityLevels.MEDIUM.value

        self.authenticator = authenticator
        self.bot_id = bot_id

    async def subscribe_to_product_feed(self, product_slug):
        await self.authenticator.register_feed_callback(commons_enums.CommunityChannelTypes.SIGNAL, self.on_new_signal,
                                                        identifier=product_slug)

    async def on_new_signal(self, parsed_message) -> None:
        try:
            signal = trading_signal_factory.create_trading_signal(parsed_message)
            self.logger.error(f"signal: {signal}")
            await self.send(signal, self.bot_id)
        except Exception as e:
            self.logger.exception(e, True, f"Error when processing signal: {e}")

    def flush(self) -> None:
        """
        Flush all instance objects reference
        """
        self.exchange_manager = None
