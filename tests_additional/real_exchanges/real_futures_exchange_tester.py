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
import octobot_trading.enums as enums
import octobot_trading.constants as constants

from tests_additional.real_exchanges import get_exchange_manager
from tests_additional.real_exchanges.real_exchange_tester import RealExchangeTester


class RealFuturesExchangeTester(RealExchangeTester):
    EXCHANGE_TYPE = enums.ExchangeTypes.FUTURE.value
    MARKET_STATUS_TYPE = "swap"

    async def test_get_funding_rate(self):
        pass

    async def get_funding_rate(self, **kwargs):
        async with self.get_exchange_manager() as exchange_manager:
            return (
                await exchange_manager.exchange.get_funding_rate(self.SYMBOL, **kwargs),
                exchange_manager.exchange.parse_funding(
                    await exchange_manager.exchange.get_price_ticker(self.SYMBOL),
                    from_ticker=True
                )
            )

    def _check_funding_rate(
        self,
        funding_rate,
        has_rate=True,
        has_last_time=True,
        has_next_rate=True,
        has_next_time=True,
        has_next_time_in_the_past=False
    ):
        """
        Used data are
        - funding rate (value)
        - last_updated (timestamp)
        - predicted_funding_rate (value)
        - next_update (timestamp)
        """
        assert funding_rate
        if has_rate:
            assert funding_rate[enums.ExchangeConstantsFundingColumns.FUNDING_RATE.value] \
                   and not funding_rate[enums.ExchangeConstantsFundingColumns.FUNDING_RATE.value].is_nan()
        else:
            assert funding_rate[enums.ExchangeConstantsFundingColumns.FUNDING_RATE.value].is_nan()
        if has_last_time:
            assert 0 < funding_rate[enums.ExchangeConstantsFundingColumns.LAST_FUNDING_TIME.value] <= self.get_time()
        else:
            assert funding_rate[enums.ExchangeConstantsFundingColumns.LAST_FUNDING_TIME.value] == constants.ZERO
        if has_next_rate:
            assert funding_rate[enums.ExchangeConstantsFundingColumns.PREDICTED_FUNDING_RATE.value] \
                   and not funding_rate[enums.ExchangeConstantsFundingColumns.PREDICTED_FUNDING_RATE.value].is_nan()
        else:
            assert funding_rate[enums.ExchangeConstantsFundingColumns.PREDICTED_FUNDING_RATE.value].is_nan()
        if has_next_time_in_the_past:
            assert funding_rate[enums.ExchangeConstantsFundingColumns.NEXT_FUNDING_TIME.value] < self.get_time()
        elif has_next_time:
            assert funding_rate[enums.ExchangeConstantsFundingColumns.NEXT_FUNDING_TIME.value] >= self.get_time()
        else:
            assert funding_rate[enums.ExchangeConstantsFundingColumns.NEXT_FUNDING_TIME.value] == constants.ZERO
