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

from ccxt.base.errors import NotSupported

from octobot_trading.channels import TRADES_CHANNEL
from octobot_trading.channels.trades import TradesProducer
from octobot_trading.enums import ExchangeConstantsOrderColumns


class TradesUpdater(TradesProducer):
    CHANNEL_NAME = TRADES_CHANNEL
    MAX_OLD_TRADES_TO_FETCH = 100
    TRADES_LIMIT = 10
    TRADES_REFRESH_TIME = 333

    async def init_old_trades(self):
        try:
            for symbol in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
                trades: list = await self.channel.exchange_manager.exchange.get_my_recent_trades(
                    symbol=symbol,
                    limit=self.MAX_OLD_TRADES_TO_FETCH)

                if trades:
                    await self.push(self._cleanup_trades_dict(trades))

            await asyncio.sleep(self.TRADES_REFRESH_TIME)
        except NotSupported:
            self.logger.warning(f"{self.channel.exchange_manager.exchange.name} is not supporting updates")
            await self.pause()
        except Exception as e:
            self.logger.error(f"Fail to initialize old trades : {e}")

    async def start(self):
        await self.init_old_trades()

        # Code bellow shouldn't be necessary
        # while not self.should_stop and not self.channel.is_paused:
        #     try:
        #         for symbol in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
        #             trades: list = await self.channel.exchange_manager.exchange.get_my_recent_trades(
        #                 symbol=symbol,
        #                 limit=self.TRADES_LIMIT)
        #
        #             if trades:
        #                 await self.push(self._cleanup_trades_dict(trades))
        #     except Exception as e:
        #         self.logger.error(f"Fail to update trades : {e}")
        #
        #     await asyncio.sleep(self.TRADES_REFRESH_TIME)

    def _cleanup_trades_dict(self, trades):
        for trade in trades:
            try:
                trade.pop(ExchangeConstantsOrderColumns.INFO.value)
            except KeyError as e:
                self.logger.error(f"Fail to cleanup trade dict ({e})")
        return trades

    async def resume(self) -> None:
        await super().resume()
        if not self.is_running:
            await self.run()
