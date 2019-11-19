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

from octobot_trading.constants import RECENT_TRADES_CHANNEL
from octobot_trading.channels.recent_trade import RecentTradeProducer
from octobot_trading.enums import ExchangeConstantsOrderColumns


class RecentTradeUpdater(RecentTradeProducer):
    CHANNEL_NAME = RECENT_TRADES_CHANNEL
    RECENT_TRADE_REFRESH_TIME = 5
    RECENT_TRADE_LIMIT = 20  # should be < to RecentTradesManager's MAX_TRADES_COUNT

    async def init_recent_trades(self):
        try:
            for pair in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
                recent_trades = await self.channel.exchange_manager.exchange.get_recent_trades(pair,
                                                                                               limit=self.RECENT_TRADE_LIMIT)
                await self.push(pair,
                                self.__cleanup_trades_dict(recent_trades),
                                partial=True)
            await asyncio.sleep(self.RECENT_TRADE_REFRESH_TIME)
        except Exception as e:
            self.logger.exception(f"Fail to initialize recent trades : {e}")

    async def start(self):
        await self.init_recent_trades()

        while not self.should_stop and not self.channel.is_paused:
            try:
                for pair in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
                    recent_trades = await self.channel.exchange_manager.exchange.get_recent_trades(pair,
                                                                                                   limit=self.RECENT_TRADE_LIMIT)
                    try:
                        await self.push(pair,
                                        self.__cleanup_trades_dict(recent_trades),
                                        partial=True)
                    except TypeError:
                        pass
                await asyncio.sleep(self.RECENT_TRADE_REFRESH_TIME)
            except NotSupported:
                self.logger.warning(f"{self.channel.exchange_manager.exchange.name} is not supporting updates")
                await self.pause()
            except Exception as e:
                self.logger.exception(f"Fail to update recent trades : {e}")

    def __cleanup_trades_dict(self, recent_trades):
        try:
            for trade in recent_trades:
                trade.pop(ExchangeConstantsOrderColumns.INFO.value)
                trade.pop(ExchangeConstantsOrderColumns.DATETIME.value)
                trade.pop(ExchangeConstantsOrderColumns.ID.value)
                trade.pop(ExchangeConstantsOrderColumns.ORDER.value)
                trade.pop(ExchangeConstantsOrderColumns.SYMBOL.value)
                trade.pop(ExchangeConstantsOrderColumns.COST.value)
                trade.pop(ExchangeConstantsOrderColumns.FEE.value)
                trade.pop(ExchangeConstantsOrderColumns.TYPE.value)
                trade.pop(ExchangeConstantsOrderColumns.TAKERORMAKER.value)
        except KeyError as e:
            self.logger.error(f"Fail to cleanup recent trades dict ({e})")
        return recent_trades

    async def resume(self) -> None:
        await super().resume()
        if not self.is_running:
            await self.run()
