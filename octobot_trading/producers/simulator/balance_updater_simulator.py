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

from octobot_trading.producers.balance_updater import (
    BalanceUpdater,
    BalanceProfitabilityUpdater,
)


class BalanceUpdaterSimulator(BalanceUpdater):
    """
    The Balance Update Simulator fetch the exchange portfolio and send it to the Balance Channel
    """

    async def fetch_portfolio(self):
        """
        Wait for its consumer to be ready and fetch portfolio from exchange
        """
        await self.wait_for_processing()
        await super(BalanceUpdater, self).fetch_portfolio()


class BalanceProfitabilityUpdaterSimulator(BalanceProfitabilityUpdater):
    """
    The Balance Profitability Updater Simulator triggers the portfolio profitability calculation
    by subscribing to Ticker and Balance channel updates
    """

    async def handle_balance_update(
        self, exchange: str, exchange_id: str, balance: dict
    ) -> None:
        """
        Balance channel consumer callback
        :param exchange: the exchange name
        :param exchange_id: the exchange id
        :param balance: the balance dict
        """
        await self.wait_for_processing()
        await super(BalanceProfitabilityUpdater, self).handle_balance_update(
            exchange=exchange, exchange_id=exchange_id, balance=balance
        )

    async def handle_ticker_update(
        self,
        exchange: str,
        exchange_id: str,
        cryptocurrency: str,
        symbol: str,
        ticker: dict,
    ) -> None:
        """
       Ticker channel consumer callback
       :param exchange: the exchange name
       :param exchange_id: the exchange id
       :param cryptocurrency: the related currency
       :param symbol: the related symbol
       :param ticker: the ticker dict
       """
        await self.wait_for_processing()
        await super(BalanceProfitabilityUpdater, self).handle_ticker_update(
            exchange=exchange,
            exchange_id=exchange_id,
            cryptocurrency=cryptocurrency,
            symbol=symbol,
            ticker=ticker,
        )
