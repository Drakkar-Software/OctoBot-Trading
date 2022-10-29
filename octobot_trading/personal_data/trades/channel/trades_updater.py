# pylint: disable=E0611
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

import octobot_commons.tree as commons_tree
import octobot_commons.enums as commons_enums
import octobot_commons.constants as commons_constants

import octobot_trading.errors as errors
import octobot_trading.personal_data.trades.channel as trades_channel
import octobot_trading.constants as constants
import octobot_trading.util as util


class TradesUpdater(trades_channel.TradesProducer):
    """
    The Trades Update fetch the exchange trades and send it to the Trade Channel
    """

    """
    The updater related channel name
    """
    CHANNEL_NAME = constants.TRADES_CHANNEL

    """
    Trades history request limit
    """
    MAX_OLD_TRADES_TO_FETCH = 100
    TRADES_LIMIT = 10

    """
    The default trade history update refresh time in seconds
    """
    TRADES_REFRESH_TIME = 333

    DEPENDENCIES_TIMEOUT = 5 * commons_constants.MINUTE_TO_SECONDS

    def __init__(self, channel):
        super().__init__(channel)

        self._is_initialized_event_set = False

    async def init_trade_history(self):
        try:
            await self.fetch_and_push()
            await asyncio.sleep(self.TRADES_REFRESH_TIME)
        except errors.NotSupported:
            self.logger.warning(f"{self.channel.exchange_manager.exchange_name} is not supporting updates")
            await self.pause()
        except Exception as e:
            self.logger.error(f"Fail to initialize trade history : {e}")

    async def fetch_and_push(self):
        for symbol in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
            trades: list = await self.channel.exchange_manager.exchange.get_my_recent_trades(
                symbol=symbol,
                limit=self.MAX_OLD_TRADES_TO_FETCH)

            if trades:
                await self.push(list(map(self.channel.exchange_manager.exchange.clean_trade, trades)))
            if not self._is_initialized_event_set:
                self._set_initialized_event(symbol)
        self._is_initialized_event_set = True

    def _set_initialized_event(self, symbol):
        # set init in updater as it's the only place we know if we fetched trades or not regardless of trades existence
        commons_tree.EventProvider.instance().trigger_event(
            self.channel.exchange_manager.bot_id, commons_tree.get_exchange_path(
                self.channel.exchange_manager.exchange_name,
                commons_enums.InitializationEventExchangeTopics.TRADES.value,
                symbol=symbol
            )
        )

    async def start(self):
        if util.is_trade_history_loading_enabled(self.channel.exchange_manager.config):
            await self.wait_for_dependencies(
                [
                    commons_tree.get_exchange_path(
                        self.channel.exchange_manager.exchange_name,
                        commons_enums.InitializationEventExchangeTopics.CONTRACTS.value
                    ),
                ],
                self.DEPENDENCIES_TIMEOUT
            )
            await self.init_trade_history()

        # Code bellow shouldn't be necessary
        # while not self.should_stop and not self.channel.is_paused:
        #     try:
        #         for symbol in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
        #             trades: list = await self.channel.exchange_manager.exchange.get_my_recent_trades(
        #                 symbol=symbol,
        #                 limit=self.TRADES_LIMIT)
        #
        #             if trades:
        #                 await self.push(list(map(self.channel.exchange_manager.exchange.clean_trade, trades)))
        #     except Exception as e:
        #         self.logger.error(f"Fail to update trades : {e}")
        #
        #     await asyncio.sleep(self.TRADES_REFRESH_TIME)

    async def resume(self) -> None:
        """
        Resume updater process
        """
        await super().resume()
        if not self.is_running:
            await self.run()
