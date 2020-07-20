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

"""
Handles balance changes
"""
from asyncio import CancelledError

from octobot_trading.channels.exchange_channel import ExchangeChannel, ExchangeChannelProducer, ExchangeChannelConsumer
from octobot_trading.constants import BALANCE_CHANNEL


class BalanceProducer(ExchangeChannelProducer):
    async def push(self, balance):
        await self.perform(balance)

    async def perform(self, balance):
        try:
            changed = await self.channel.exchange_manager.exchange_personal_data.handle_portfolio_update(
                balance=balance, should_notify=False)
            if changed:
                await self.send(balance)
        except CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.exception(e, True, f"Exception when triggering update: {e}")

    async def send(self, balance):
        for consumer in self.channel.get_filtered_consumers():
            await consumer.queue.put({
                "exchange": self.channel.exchange_manager.exchange_name,
                "exchange_id": self.channel.exchange_manager.id,
                "balance": balance
            })

    async def refresh_real_trader_portfolio(self, force_manual_refresh=False) -> bool:
        if force_manual_refresh or self.channel.exchange_manager.requires_refresh_trigger(BALANCE_CHANNEL):
            self.logger.debug(f"Refreshing portfolio from {self.channel.exchange_manager.get_exchange_name()} exchange")
            return await self._update_portfolio_from_exchange()
        else:
            self.logger.debug(f"Portfolio refresh from {self.channel.exchange_manager.get_exchange_name()} exchange "
                              f"will automatically be performed")
        return False

    async def _update_portfolio_from_exchange(self, should_notify=False) -> bool:
        """
        Update portfolio from exchange
        :param should_notify: if Orders channel consumers should be notified
        :return: True if the portfolio was updated
        """
        balance = await self.channel.exchange_manager.exchange.get_balance()
        return await self.channel.exchange_manager.exchange_personal_data.handle_portfolio_update(
            balance=balance, should_notify=should_notify)


class BalanceChannel(ExchangeChannel):
    PRODUCER_CLASS = BalanceProducer
    CONSUMER_CLASS = ExchangeChannelConsumer


class BalanceProfitabilityProducer(ExchangeChannelProducer):
    async def push(self, balance, mark_price):
        await self.perform(balance, mark_price)

    async def perform(self, balance, mark_price):
        try:
            await self.channel.exchange_manager.exchange_personal_data \
                .handle_portfolio_profitability_update(balance, mark_price, should_notify=True)
        except CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.exception(e, True, f"Exception when triggering update: {e}")

    async def send(self, profitability, profitability_percent,
                   market_profitability_percent,
                   initial_portfolio_current_profitability):
        for consumer in self.channel.get_filtered_consumers():
            await consumer.queue.put({
                "exchange": self.channel.exchange_manager.exchange_name,
                "exchange_id": self.channel.exchange_manager.id,
                "profitability": profitability,
                "profitability_percent": profitability_percent,
                "market_profitability_percent": market_profitability_percent,
                "initial_portfolio_current_profitability": initial_portfolio_current_profitability
            })


class BalanceProfitabilityChannel(ExchangeChannel):
    PRODUCER_CLASS = BalanceProfitabilityProducer
    CONSUMER_CLASS = ExchangeChannelConsumer
