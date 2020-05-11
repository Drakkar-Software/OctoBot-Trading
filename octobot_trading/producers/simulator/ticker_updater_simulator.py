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
from octobot_backtesting.api.importer import get_available_data_types
from octobot_backtesting.data import DataBaseNotExists
from octobot_backtesting.enums import ExchangeDataTables
from octobot_channels.channels.channel import get_chan
from octobot_commons.enums import PriceIndexes

from octobot_commons.channels_name import OctoBotBacktestingChannelsName
from octobot_trading.constants import OHLCV_CHANNEL
from octobot_trading.enums import ExchangeConstantsTickersColumns
from octobot_trading.channels.exchange_channel import get_chan as get_exchange_chan
from octobot_trading.producers.simulator.simulator_updater_utils import stop_and_pause
from octobot_trading.producers.ticker_updater import TickerUpdater


class TickerUpdaterSimulator(TickerUpdater):
    def __init__(self, channel, importer):
        super().__init__(channel)
        self.exchange_data_importer = importer
        self.exchange_name = self.channel.exchange_manager.exchange_name

        self.last_timestamp_pushed = 0
        self.last_timestamp_pushed_by_symbol = {}
        self.time_consumer = None
        # Only generate tickers from the shortest handled time frame
        self.ticker_time_frame = self.channel.exchange_manager.exchange_config.get_shortest_time_frame().value

    async def start(self):
        await self.resume()

    async def handle_timestamp(self, timestamp, **kwargs):
        try:
            for pair in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
                ticker_data = (await self.exchange_data_importer.get_ticker_from_timestamps(exchange_name=self.exchange_name,
                                                                                            symbol=pair,
                                                                                            inferior_timestamp=timestamp,
                                                                                            limit=1))[0]
                if ticker_data[0] > self.last_timestamp_pushed:
                    self.last_timestamp_pushed = ticker_data[0]
                    await self.push(pair, ticker_data[-1])
        except DataBaseNotExists as e:
            self.logger.warning(f"Not enough data : {e}")
            await self.pause()
            await self.stop()
        except IndexError as e:
            self.logger.warning(f"Failed to access ticker_data : {e}")

    async def _ticker_from_ohlcv_callback(self, exchange: str, exchange_id: str,
                                          cryptocurrency: str, symbol: str, time_frame, candle):
        if self.ticker_time_frame == time_frame and candle:
            last_candle_timestamp = candle[PriceIndexes.IND_PRICE_TIME.value]
            if last_candle_timestamp > self.last_timestamp_pushed_by_symbol[symbol]:
                self.last_timestamp_pushed_by_symbol[symbol] = last_candle_timestamp
                ticker = self._generate_ticker_from_candle(candle, symbol, last_candle_timestamp)
                await self.push(symbol, ticker)

    @staticmethod
    def _generate_ticker_from_candle(candle, symbol, last_candle_timestamp):
        return {
            ExchangeConstantsTickersColumns.TIMESTAMP.value: last_candle_timestamp,
            ExchangeConstantsTickersColumns.LAST.value: candle[PriceIndexes.IND_PRICE_CLOSE.value],
            ExchangeConstantsTickersColumns.SYMBOL.value: symbol,
            ExchangeConstantsTickersColumns.HIGH.value: candle[PriceIndexes.IND_PRICE_HIGH.value],
            ExchangeConstantsTickersColumns.LOW.value: candle[PriceIndexes.IND_PRICE_LOW.value],
            ExchangeConstantsTickersColumns.OPEN.value: candle[PriceIndexes.IND_PRICE_OPEN.value],
            ExchangeConstantsTickersColumns.CLOSE.value: candle[PriceIndexes.IND_PRICE_CLOSE.value]
        }

    async def pause(self):
        if self.time_consumer is not None:
            await get_chan(OctoBotBacktestingChannelsName.TIME_CHANNEL.value).remove_consumer(self.time_consumer)
        self.is_running = False

    async def stop(self):
        await stop_and_pause(self)

    async def resume(self):
        if not self.is_running:
            if self.time_consumer is None and not self.channel.is_paused:
                if ExchangeDataTables.TICKER in get_available_data_types(self.exchange_data_importer):
                    self.time_consumer = await get_chan(OctoBotBacktestingChannelsName.TIME_CHANNEL.value).new_consumer(
                        self.handle_timestamp)
                else:
                    await get_exchange_chan(OHLCV_CHANNEL,
                                            self.channel.exchange_manager.id)\
                        .new_consumer(self._ticker_from_ohlcv_callback)
                    self.last_timestamp_pushed_by_symbol = {
                        symbol: 0
                        for symbol in self.channel.exchange_manager.exchange_config.traded_symbol_pairs
                    }
                self.is_running = True
