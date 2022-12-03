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
import os

import pytest
from mock import patch
from datetime import datetime

from octobot_commons.asyncio_tools import wait_asyncio_next_cycle
from octobot_commons.constants import MSECONDS_TO_MINUTE
from octobot_commons.enums import TimeFrames, TimeFramesMinutes
from octobot_commons.tests.test_config import load_test_config
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.exchanges.exchanges import Exchanges
from octobot_trading.api.exchange import cancel_ccxt_throttle_task
from tests import event_loop

pytestmark = pytest.mark.asyncio


MS_TIMESTAMP = round((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000)


def get_constant_ms_timestamp():
    return MS_TIMESTAMP


class TestExchanges:
    @staticmethod
    async def init_default():
        return load_test_config()

    async def test_add_exchange(self):
        config = await self.init_default()

        exchange_manager_binanceus = ExchangeManager(config, "binanceus")
        await exchange_manager_binanceus.initialize()
        Exchanges.instance().add_exchange(exchange_manager_binanceus, "")

        exchange_manager_bitmex = ExchangeManager(config, "bitmex")
        await exchange_manager_bitmex.initialize()
        Exchanges.instance().add_exchange(exchange_manager_bitmex, "")

        exchange_manager_bybit = ExchangeManager(config, "bybit")
        await exchange_manager_bybit.initialize()
        Exchanges.instance().add_exchange(exchange_manager_bybit, "")

        assert "binanceus" in Exchanges.instance().exchanges
        assert "bitmex" in Exchanges.instance().exchanges
        assert "bybit" in Exchanges.instance().exchanges
        assert "test" not in Exchanges.instance().exchanges

        await exchange_manager_binanceus.stop()
        await exchange_manager_bitmex.stop()
        await exchange_manager_bybit.stop()
        cancel_ccxt_throttle_task()
        # let updaters gracefully shutdown
        await wait_asyncio_next_cycle()

    async def test_get_exchange(self):
        config = await self.init_default()

        exchange_manager_binanceus = ExchangeManager(config, "binanceus")
        await exchange_manager_binanceus.initialize()
        Exchanges.instance().add_exchange(exchange_manager_binanceus, "")

        exchange_manager_bitmex = ExchangeManager(config, "bitmex")
        await exchange_manager_bitmex.initialize()
        Exchanges.instance().add_exchange(exchange_manager_bitmex, "")

        exchange_manager_bybit = ExchangeManager(config, "bybit")
        await exchange_manager_bybit.initialize()
        Exchanges.instance().add_exchange(exchange_manager_bybit, "")

        assert Exchanges.instance().get_exchanges_list("binanceus")[0].exchange_manager is exchange_manager_binanceus
        assert Exchanges.instance().get_exchanges_list("bitmex")[0].exchange_manager is exchange_manager_bitmex
        assert Exchanges.instance().get_exchanges_list("bybit")[0].exchange_manager is exchange_manager_bybit

        with pytest.raises(KeyError):
            assert Exchanges.instance().get_exchanges_list("test")

        await exchange_manager_binanceus.stop()
        await exchange_manager_bitmex.stop()
        await exchange_manager_bybit.stop()
        cancel_ccxt_throttle_task()
        # let updaters gracefully shutdown
        await wait_asyncio_next_cycle()

    async def test_del_exchange(self):
        config = await self.init_default()

        exchange_manager_binanceus = ExchangeManager(config, "binanceus")
        await exchange_manager_binanceus.initialize()
        Exchanges.instance().add_exchange(exchange_manager_binanceus, "")

        exchange_manager_bitmex = ExchangeManager(config, "bitmex")
        await exchange_manager_bitmex.initialize()
        Exchanges.instance().add_exchange(exchange_manager_bitmex, "")

        exchange_manager_bybit = ExchangeManager(config, "bybit")
        await exchange_manager_bybit.initialize()
        Exchanges.instance().add_exchange(exchange_manager_bybit, "")

        Exchanges.instance().del_exchange("binanceus", exchange_manager_binanceus.id)
        assert "binanceus" not in Exchanges.instance().exchanges
        Exchanges.instance().del_exchange("bitmex", exchange_manager_bitmex.id)
        assert "bitmex" not in Exchanges.instance().exchanges
        Exchanges.instance().del_exchange("bybit", exchange_manager_bybit.id)
        assert "bybit" not in Exchanges.instance().exchanges

        Exchanges.instance().del_exchange("test", "")  # should not raise

        assert Exchanges.instance().exchanges == {}
        await exchange_manager_binanceus.stop()
        await exchange_manager_bitmex.stop()
        await exchange_manager_bybit.stop()
        cancel_ccxt_throttle_task()
        # let updaters gracefully shutdown
        await wait_asyncio_next_cycle()

    async def test_get_all_exchanges(self):
        config = await self.init_default()

        exchange_manager_binanceus = ExchangeManager(config, "binanceus")
        await exchange_manager_binanceus.initialize()
        Exchanges.instance().add_exchange(exchange_manager_binanceus, "")

        exchange_manager_bitmex = ExchangeManager(config, "bitmex")
        await exchange_manager_bitmex.initialize()
        Exchanges.instance().add_exchange(exchange_manager_bitmex, "")

        exchange_manager_bybit = ExchangeManager(config, "bybit")
        await exchange_manager_bybit.initialize()
        Exchanges.instance().add_exchange(exchange_manager_bybit, "")

        exchanges = Exchanges.instance().get_all_exchanges()
        assert exchanges[0].exchange_manager is exchange_manager_binanceus
        assert exchanges[1].exchange_manager is exchange_manager_bitmex
        assert exchanges[2].exchange_manager is exchange_manager_bybit

        await exchange_manager_binanceus.stop()
        await exchange_manager_bitmex.stop()
        await exchange_manager_bybit.stop()
        cancel_ccxt_throttle_task()
        # let updaters gracefully shutdown
        await wait_asyncio_next_cycle()

    async def test_ms_timestamp_operations(self):
        config = await self.init_default()
        exchange_manager_bitmex = ExchangeManager(config, "bitmex")
        await exchange_manager_bitmex.initialize()

        if os.getenv('CYTHON_IGNORE'):
            await exchange_manager_bitmex.stop()
            return

        exchange = exchange_manager_bitmex.exchange
        with patch.object(exchange, 'get_exchange_current_time', new=get_constant_ms_timestamp):
            expected_ms_timestamp = MS_TIMESTAMP - TimeFramesMinutes[TimeFrames.ONE_HOUR] * MSECONDS_TO_MINUTE * 200
            assert exchange.get_candle_since_timestamp(TimeFrames.ONE_HOUR, count=200) == expected_ms_timestamp

            expected_ms_timestamp = MS_TIMESTAMP - TimeFramesMinutes[TimeFrames.ONE_WEEK] * MSECONDS_TO_MINUTE * 200
            assert exchange.get_candle_since_timestamp(TimeFrames.ONE_WEEK, count=200) == expected_ms_timestamp

            expected_ms_timestamp = MS_TIMESTAMP - TimeFramesMinutes[TimeFrames.ONE_MONTH] * MSECONDS_TO_MINUTE * 2000
            assert exchange.get_candle_since_timestamp(TimeFrames.ONE_MONTH, count=2000) == expected_ms_timestamp

            expected_ms_timestamp = MS_TIMESTAMP - TimeFramesMinutes[TimeFrames.ONE_MINUTE] * MSECONDS_TO_MINUTE * 10
            assert exchange.get_candle_since_timestamp(TimeFrames.ONE_MINUTE, count=10) == expected_ms_timestamp

            expected_ms_timestamp = MS_TIMESTAMP - TimeFramesMinutes[TimeFrames.ONE_MINUTE] * MSECONDS_TO_MINUTE * 0
            assert exchange.get_candle_since_timestamp(TimeFrames.ONE_MINUTE, count=0) == expected_ms_timestamp

            # 2000 months into the future
            expected_ms_timestamp = MS_TIMESTAMP + TimeFramesMinutes[TimeFrames.ONE_MONTH] * MSECONDS_TO_MINUTE * 2000
            assert exchange.get_candle_since_timestamp(TimeFrames.ONE_MONTH, count=-2000) == expected_ms_timestamp
        await exchange_manager_bitmex.stop()
