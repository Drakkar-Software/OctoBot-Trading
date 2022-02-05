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
import decimal

import octobot_commons.logging as logging

import octobot_trading.errors as errors
import octobot_trading.constants as constants
import octobot_trading.personal_data.portfolios.channel.balance as portfolios_channel
import octobot_trading.exchange_channel as exchange_channel


class BalanceUpdater(portfolios_channel.BalanceProducer):
    """
    The Balance Update fetch the exchange portfolio and send it to the Balance Channel
    """

    """
    The default balance update refresh time in seconds
    """
    BALANCE_REFRESH_TIME = 666

    """
    The updater related channel name
    """
    CHANNEL_NAME = constants.BALANCE_CHANNEL

    async def start(self) -> None:
        """
        Starts the balance updating process
        """
        while not self.should_stop:
            try:
                await self.fetch_and_push()
                await asyncio.sleep(self.BALANCE_REFRESH_TIME)
            except errors.NotSupported:
                self.logger.warning(
                    f"{self.channel.exchange_manager.exchange_name} is not supporting updates"
                )
                await self.pause()
            except Exception as e:
                self.logger.error(f"Failed to update balance : {e}")

    async def fetch_and_push(self):
        await self.push((await self.fetch_portfolio()))

    async def fetch_portfolio(self):
        """
        Fetch portfolio from exchange
        """
        return await self.channel.exchange_manager.exchange.get_balance()

    async def resume(self) -> None:
        """
        Resume updater process
        """
        await super().resume()
        if not self.is_running:
            await self.run()


class BalanceProfitabilityUpdater(portfolios_channel.BalanceProfitabilityProducer):
    """
    The Balance Profitability Updater triggers the portfolio profitability calculation
    by subscribing to Mark price and Balance channel updates
    """

    """
    The updater related channel name
    """
    CHANNEL_NAME = constants.BALANCE_PROFITABILITY_CHANNEL

    def __init__(self, channel):
        super().__init__(channel)
        self.logger = logging.get_logger(self.__class__.__name__)
        self.exchange_personal_data = (
            self.channel.exchange_manager.exchange_personal_data
        )
        self.balance_consumer = None
        self.mark_price_consumer = None

    async def start(self) -> None:
        """
        Starts the balance profitability subscribing process
        """
        self.balance_consumer = await exchange_channel.get_chan(
            constants.BALANCE_CHANNEL, self.channel.exchange_manager.id
        ).new_consumer(self.handle_balance_update)
        self.mark_price_consumer = await exchange_channel.get_chan(
            constants.MARK_PRICE_CHANNEL, self.channel.exchange_manager.id
        ).new_consumer(self.handle_mark_price_update)

    async def stop(self) -> None:
        """
        Stop and remove the balance profitability consumers
        """
        await super().stop()
        try:
            await exchange_channel.get_chan(
                constants.BALANCE_CHANNEL, self.channel.exchange_manager.id
            ).remove_consumer(self.balance_consumer)
        except KeyError:
            # balance channel might already be stopped and removed from available channels
            pass
        try:
            await exchange_channel.get_chan(
                constants.MARK_PRICE_CHANNEL, self.channel.exchange_manager.id
            ).remove_consumer(self.mark_price_consumer)
        except KeyError:
            # balance channel might already be stopped and removed from available channels
            pass
        self.balance_consumer = None
        self.mark_price_consumer = None

    async def handle_balance_update(
        self, exchange: str, exchange_id: str, balance: dict
    ) -> None:
        """
        Balance channel consumer callback
        :param exchange: the exchange name
        :param exchange_id: the exchange id
        :param balance: the balance dict
        """
        try:
            await self.exchange_personal_data.handle_portfolio_profitability_update(
                balance=balance, mark_price=None, symbol=None
            )
        except Exception as e:
            self.logger.exception(e, True, f"Fail to handle balance update : {e}")

    async def handle_mark_price_update(
        self,
        exchange: str,
        exchange_id: str,
        cryptocurrency: str,
        symbol: str,
        mark_price: decimal.Decimal,
    ) -> None:
        """
        Mark price channel consumer callback
        :param exchange: the exchange name
        :param exchange_id: the exchange id
        :param cryptocurrency: the related currency
        :param symbol: the related symbol
        :param mark_price: the mark price
        """
        try:
            await self.exchange_personal_data.handle_portfolio_profitability_update(
                symbol=symbol, mark_price=mark_price, balance=None
            )
        except Exception as e:
            self.logger.exception(e, True, f"Fail to handle mark price update : {e}")
