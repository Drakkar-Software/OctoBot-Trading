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
import pytest

from octobot_commons.tests.test_config import load_test_config
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.exchanges.exchanges import Exchanges

pytestmark = pytest.mark.asyncio


class TestExchanges:
    @staticmethod
    async def init_default():
        return load_test_config()

    async def test_add_exchange(self):
        config = await self.init_default()

        exchange_manager_binance = ExchangeManager(config, "binance")
        await exchange_manager_binance.initialize()
        Exchanges.instance().add_exchange(exchange_manager_binance)

        exchange_manager_bitmex = ExchangeManager(config, "bitmex")
        await exchange_manager_bitmex.initialize()
        Exchanges.instance().add_exchange(exchange_manager_bitmex)

        exchange_manager_poloniex = ExchangeManager(config, "poloniex")
        await exchange_manager_poloniex.initialize()
        Exchanges.instance().add_exchange(exchange_manager_poloniex)

        assert "binance" in Exchanges.instance().exchanges
        assert "bitmex" in Exchanges.instance().exchanges
        assert "poloniex" in Exchanges.instance().exchanges
        assert "test" not in Exchanges.instance().exchanges

        await exchange_manager_binance.stop()
        await exchange_manager_bitmex.stop()
        await exchange_manager_poloniex.stop()

    async def test_get_exchange(self):
        config = await self.init_default()

        exchange_manager_binance = ExchangeManager(config, "binance")
        await exchange_manager_binance.initialize()
        Exchanges.instance().add_exchange(exchange_manager_binance)

        exchange_manager_bitmex = ExchangeManager(config, "bitmex")
        await exchange_manager_bitmex.initialize()
        Exchanges.instance().add_exchange(exchange_manager_bitmex)

        exchange_manager_poloniex = ExchangeManager(config, "poloniex")
        await exchange_manager_poloniex.initialize()
        Exchanges.instance().add_exchange(exchange_manager_poloniex)

        assert Exchanges.instance().get_exchange("binance").exchange_manager is exchange_manager_binance
        assert Exchanges.instance().get_exchange("bitmex").exchange_manager is exchange_manager_bitmex
        assert Exchanges.instance().get_exchange("poloniex").exchange_manager is exchange_manager_poloniex

        with pytest.raises(KeyError):
            assert Exchanges.instance().get_exchange("test")

        await exchange_manager_binance.stop()
        await exchange_manager_bitmex.stop()
        await exchange_manager_poloniex.stop()

    async def test_del_exchange(self):
        config = await self.init_default()

        exchange_manager_binance = ExchangeManager(config, "binance")
        await exchange_manager_binance.initialize()
        Exchanges.instance().add_exchange(exchange_manager_binance)

        exchange_manager_bitmex = ExchangeManager(config, "bitmex")
        await exchange_manager_bitmex.initialize()
        Exchanges.instance().add_exchange(exchange_manager_bitmex)

        exchange_manager_poloniex = ExchangeManager(config, "poloniex")
        await exchange_manager_poloniex.initialize()
        Exchanges.instance().add_exchange(exchange_manager_poloniex)

        Exchanges.instance().del_exchange("binance")
        assert "binance" not in Exchanges.instance().exchanges
        Exchanges.instance().del_exchange("bitmex")
        assert "bitmex" not in Exchanges.instance().exchanges
        Exchanges.instance().del_exchange("poloniex")
        assert "poloniex" not in Exchanges.instance().exchanges

        Exchanges.instance().del_exchange("test")  # should not raise

        assert Exchanges.instance().exchanges == {}
        await exchange_manager_binance.stop()
        await exchange_manager_bitmex.stop()
        await exchange_manager_poloniex.stop()
