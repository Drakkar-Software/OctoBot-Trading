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
from octobot_trading.channels.exchange_channel import get_chan
from octobot_trading.channels.price import MarkPriceProducer
from octobot_trading.constants import MARK_PRICE_CHANNEL, RECENT_TRADES_CHANNEL, TICKER_CHANNEL
from octobot_trading.data_manager.prices_manager import PricesManager
from octobot_trading.enums import ExchangeConstantsTickersColumns, ExchangeConstantsOrderColumns


class MarkPriceUpdater(MarkPriceProducer):
    CHANNEL_NAME = MARK_PRICE_CHANNEL

    async def start(self):
        await get_chan(RECENT_TRADES_CHANNEL, self.channel.exchange_manager.id)\
            .new_consumer(self.handle_recent_trades_update)
        await get_chan(TICKER_CHANNEL, self.channel.exchange_manager.id).new_consumer(self.handle_ticker_update)

    """
    Recent trades channel consumer callback
    """

    async def handle_recent_trades_update(self, exchange: str, exchange_id: str, symbol: str, recent_trades: list):
        try:
            mark_price = PricesManager.calculate_mark_price_from_recent_trade_prices(
                [float(last_price[ExchangeConstantsOrderColumns.PRICE.value])
                 for last_price in recent_trades])

            await self.push(symbol, mark_price)
        except Exception as e:
            self.logger.exception(e, True, f"Fail to handle recent trades update : {e}")

    """
    Ticker channel consumer callback
    """

    async def handle_ticker_update(self, exchange: str, exchange_id: str, symbol: str, ticker: dict):
        try:
            await self.push(symbol, ticker[ExchangeConstantsTickersColumns.CLOSE.value])
        except Exception as e:
            self.logger.exception(e, True, f"Fail to handle ticker update : {e}")
