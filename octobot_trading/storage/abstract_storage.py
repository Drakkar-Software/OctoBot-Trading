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
#  License along with this library
import octobot_commons.display as commons_display

import octobot_trading.exchange_channel as exchanges_channel


class AbstractStorage:
    IS_LIVE_CONSUMER = True
    USE_LIVE_CONSUMER_IN_BACKTESTING = False
    LIVE_CHANNEL = None
    IS_HISTORICAL = True

    def __init__(self, exchange_manager, plot_settings: commons_display.PlotSettings,
                 use_live_consumer_in_backtesting=None, is_historical=None):
        self.exchange_manager = exchange_manager
        self.plot_settings: commons_display.PlotSettings = plot_settings
        self.consumer = None
        self.use_live_consumer_in_backtesting = use_live_consumer_in_backtesting \
            or self.USE_LIVE_CONSUMER_IN_BACKTESTING
        self.is_historical = is_historical or self.IS_HISTORICAL

    def should_register_live_consumer(self):
        return self.IS_LIVE_CONSUMER and \
           (
                not self.exchange_manager.is_backtesting or
                (self.exchange_manager.is_backtesting and self.use_live_consumer_in_backtesting)
            )

    async def start(self):
        if self.should_register_live_consumer():
            await self.register_live_consumer()
        await self.on_start()

    async def on_start(self):
        """
        Called after start, implement in necessary
        """
        pass

    async def register_live_consumer(self):
        if self.LIVE_CHANNEL is None:
            raise ValueError(f"self.live_channel has to be set")
        self.consumer = await exchanges_channel.get_chan(
            self.LIVE_CHANNEL,
            self.exchange_manager.id
        ).new_consumer(
            self._live_callback
        )

    async def stop(self):
        if self.consumer is not None:
            await self.consumer.stop()
        self.consumer = None
        self.exchange_manager = None

    async def _live_callback(self, *args, **kwargs):
        raise NotImplementedError(f"_live_callback not implemented for {self.__class__.__name__}")

    async def store_history(self):
        raise NotImplementedError(f"store_history not implemented for {self.__class__.__name__}")
