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
from octobot_trading.constants import TICKER_CHANNEL, RECENT_TRADES_CHANNEL
from octobot_trading.exchanges.exchange_simulator import get_real_available_data, handles_real_data_for_updater
from octobot_trading.producers.prices_updater import MarkPriceUpdater
from octobot_trading.channels.exchange_channel import get_chan


class MarkPriceUpdaterSimulator(MarkPriceUpdater):
    def __init__(self, channel, importer):
        super().__init__(channel)
        self.exchange_data_importer = importer

    async def start(self):
        exchange = self.channel.exchange_manager.exchange
        available_data = get_real_available_data(exchange.exchange_importers)
        real_data_for_recent_trades = handles_real_data_for_updater(RECENT_TRADES_CHANNEL, available_data)
        real_data_for_ticker = handles_real_data_for_updater(TICKER_CHANNEL, available_data)
        # if recent trades and ticker channels are both generated from ohlcv, do not watch them both,
        # prefer recent trades
        if real_data_for_recent_trades or not (real_data_for_recent_trades or real_data_for_ticker):
            await get_chan(RECENT_TRADES_CHANNEL, self.channel.exchange_manager.id) \
                .new_consumer(self.handle_recent_trades_update)
        if real_data_for_ticker:
            await get_chan(TICKER_CHANNEL, self.channel.exchange_manager.id).new_consumer(self.handle_ticker_update)
