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
import time

from ccxt.base.errors import NotSupported
from octobot_commons.constants import HOURS_TO_SECONDS

from octobot_trading.constants import FUNDING_CHANNEL
from octobot_trading.channels.funding import FundingProducer
from octobot_trading.enums import ExchangeConstantsFundingColumns


class FundingUpdater(FundingProducer):
    CHANNEL_NAME = FUNDING_CHANNEL

    FUNDING_REFRESH_TIME = 2 * HOURS_TO_SECONDS
    FUNDING_REFRESH_TIME_MIN = 0.2 * HOURS_TO_SECONDS
    FUNDING_REFRESH_TIME_MAX = 8 * HOURS_TO_SECONDS

    async def start(self):
        if not self._should_run():
            return

        while not self.should_stop and not self.channel.is_paused:
            next_funding_time = None
            sleep_time = self.FUNDING_REFRESH_TIME_MIN
            try:
                for pair in self.channel.exchange_manager.exchange_config.traded_symbol_pairs:
                    next_funding_time_candidate = await self.fetch_symbol_funding_rate(pair)
                    if next_funding_time_candidate is not None:
                        next_funding_time = next_funding_time_candidate
            except (NotSupported, NotImplementedError):
                self.logger.warning(f"{self.channel.exchange_manager.exchange_name} is not supporting updates")
                await self.pause()
            finally:
                if next_funding_time:
                    should_sleep_time = next_funding_time - time.time()
                    sleep_time = should_sleep_time if should_sleep_time < self.FUNDING_REFRESH_TIME_MAX else \
                        self.FUNDING_REFRESH_TIME
                await asyncio.sleep(sleep_time)

    async def fetch_symbol_funding_rate(self, symbol: str):
        try:
            funding: dict = await self.channel.exchange_manager.exchange.get_funding_rate(symbol)

            if funding:
                next_funding_time = funding[ExchangeConstantsFundingColumns.NEXT_FUNDING_TIME.value]
                await self.push(symbol=symbol,
                                funding_rate=funding[ExchangeConstantsFundingColumns.FUNDING_RATE.value],
                                next_funding_time=next_funding_time,
                                timestamp=funding[ExchangeConstantsFundingColumns.TIMESTAMP.value])
                return next_funding_time
        except (NotSupported, NotImplementedError) as ne:
            raise ne
        except Exception as e:
            self.logger.exception(e, True, f"Fail to update funding rate : {e}")
        return None

    def _should_run(self) -> bool:
        if not self.channel.exchange_manager.is_margin:
            return False
        else:
            return not self.channel.exchange_manager.exchange.FUNDING_WITH_MARK_PRICE

    async def resume(self) -> None:
        if not self._should_run():
            return
        await super().resume()
        if not self.is_running:
            await self.run()
