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

from math import nan
from octobot_commons.enums import PriceIndexes

from octobot_trading.channels import OHLCV_CHANNEL, RECENT_TRADES_CHANNEL
from octobot_trading.channels.exchange_channel import ExchangeChannels
from octobot_trading.channels.kline import KlineProducer
from octobot_trading.enums import ExchangeConstantsOrderColumns


class KlineUpdater(KlineProducer):
    def __init__(self, channel):
        super().__init__(channel)
        self.should_stop = False
        self.channel = channel

    """
    Creates OHLCV & Recent trade consumers
    """

    async def start(self):
        ExchangeChannels.get_chan(RECENT_TRADES_CHANNEL, self.channel.exchange_manager.exchange.name) \
            .new_consumer(self.recent_trades_callback)
        ExchangeChannels.get_chan(OHLCV_CHANNEL, self.channel.exchange_manager.exchange.name) \
            .new_consumer(self.ohlcv_callback)

    async def recent_trades_callback(self, symbol, recent_trades):
        try:
            kline: list = [nan] * len(PriceIndexes)
            if len(recent_trades) == 1:
                trade: dict = recent_trades[-1]
                trade_price: float = trade[ExchangeConstantsOrderColumns.PRICE.value]
                kline[PriceIndexes.IND_PRICE_VOL.value] = trade[ExchangeConstantsOrderColumns.AMOUNT.value]
                kline[PriceIndexes.IND_PRICE_HIGH.value] = trade_price
                kline[PriceIndexes.IND_PRICE_LOW.value] = trade_price
                kline[PriceIndexes.IND_PRICE_CLOSE.value] = trade_price
            else:
                trade_prices: list = [trade[ExchangeConstantsOrderColumns.PRICE.value] for trade in recent_trades]
                kline[PriceIndexes.IND_PRICE_VOL.value] = sum([trade[ExchangeConstantsOrderColumns.AMOUNT.value]
                                                               for trade in recent_trades])
                kline[PriceIndexes.IND_PRICE_HIGH.value] = max(trade_prices)
                kline[PriceIndexes.IND_PRICE_LOW.value] = min(trade_prices)
                kline[PriceIndexes.IND_PRICE_CLOSE.value] = recent_trades[-1][ExchangeConstantsOrderColumns.PRICE.value]
            for time_frame in self.channel.exchange_manager.time_frames:
                await self.push(time_frame, symbol, kline, reset=False)
        except Exception as e:
            self.logger.error(f"Failed to handle recent trade update ({e})")

    async def ohlcv_callback(self, symbol, time_frame, candle):
        try:
            await self.push(time_frame, symbol, candle, reset=True)
        except Exception as e:
            self.logger.error(f"Failed to handle ohlcv update ({e})")
