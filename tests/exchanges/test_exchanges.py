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
from tests.util import reset_exchanges_list, delete_all_channels

pytestmark = pytest.mark.asyncio


class TestExchanges:
    @staticmethod
    async def init_default(exchanges):
        reset_exchanges_list()

        for exchange in exchanges:
            delete_all_channels(exchange)

        return load_test_config()

    async def test_add_exchange(self):
        config = await self.init_default(["binance", "bitmex", "poloniex"])

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

    async def test_get_exchange(self):
        config = await self.init_default(["binance", "bitmex", "poloniex"])

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
