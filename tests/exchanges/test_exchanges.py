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

from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.exchanges.exchanges import Exchanges

# Import required fixtures
from tests import config

pytestmark = pytest.mark.asyncio


class TestExchanges:
    async def test_add_exchange(self, config):
        exchange_manager_binance = ExchangeManager(config, "binance")
        await exchange_manager_binance.initialize()
        Exchanges.instance().add_exchange(exchange_manager_binance, "")

        exchange_manager_bitmex = ExchangeManager(config, "bitmex")
        await exchange_manager_bitmex.initialize()
        Exchanges.instance().add_exchange(exchange_manager_bitmex, "")

        exchange_manager_poloniex = ExchangeManager(config, "poloniex")
        await exchange_manager_poloniex.initialize()
        Exchanges.instance().add_exchange(exchange_manager_poloniex, "")

        assert "binance" in Exchanges.instance().exchanges
        assert "bitmex" in Exchanges.instance().exchanges
        assert "poloniex" in Exchanges.instance().exchanges
        assert "test" not in Exchanges.instance().exchanges

        await exchange_manager_binance.stop()
        await exchange_manager_bitmex.stop()
        await exchange_manager_poloniex.stop()

    async def test_get_exchange(self, config):
        exchange_manager_binance = ExchangeManager(config, "binance")
        await exchange_manager_binance.initialize()
        Exchanges.instance().add_exchange(exchange_manager_binance, "")

        exchange_manager_bitmex = ExchangeManager(config, "bitmex")
        await exchange_manager_bitmex.initialize()
        Exchanges.instance().add_exchange(exchange_manager_bitmex, "")

        exchange_manager_poloniex = ExchangeManager(config, "poloniex")
        await exchange_manager_poloniex.initialize()
        Exchanges.instance().add_exchange(exchange_manager_poloniex, "")

        assert Exchanges.instance().get_exchanges_list("binance")[0].exchange_manager is exchange_manager_binance
        assert Exchanges.instance().get_exchanges_list("bitmex")[0].exchange_manager is exchange_manager_bitmex
        assert Exchanges.instance().get_exchanges_list("poloniex")[0].exchange_manager is exchange_manager_poloniex

        with pytest.raises(KeyError):
            assert Exchanges.instance().get_exchanges_list("test")

        await exchange_manager_binance.stop()
        await exchange_manager_bitmex.stop()
        await exchange_manager_poloniex.stop()

    async def test_del_exchange(self, config):
        exchange_manager_binance = ExchangeManager(config, "binance")
        await exchange_manager_binance.initialize()
        Exchanges.instance().add_exchange(exchange_manager_binance, "")

        exchange_manager_bitmex = ExchangeManager(config, "bitmex")
        await exchange_manager_bitmex.initialize()
        Exchanges.instance().add_exchange(exchange_manager_bitmex, "")

        exchange_manager_poloniex = ExchangeManager(config, "poloniex")
        await exchange_manager_poloniex.initialize()
        Exchanges.instance().add_exchange(exchange_manager_poloniex, "")

        Exchanges.instance().del_exchange("binance", exchange_manager_binance.id)
        assert "binance" not in Exchanges.instance().exchanges
        Exchanges.instance().del_exchange("bitmex", exchange_manager_bitmex.id)
        assert "bitmex" not in Exchanges.instance().exchanges
        Exchanges.instance().del_exchange("poloniex", exchange_manager_poloniex.id)
        assert "poloniex" not in Exchanges.instance().exchanges

        Exchanges.instance().del_exchange("test", "")  # should not raise

        assert Exchanges.instance().exchanges == {}
        await exchange_manager_binance.stop()
        await exchange_manager_bitmex.stop()
        await exchange_manager_poloniex.stop()

    async def test_get_all_exchanges(self, config):
        exchange_manager_binance = ExchangeManager(config, "binance")
        await exchange_manager_binance.initialize()
        Exchanges.instance().add_exchange(exchange_manager_binance, "")

        exchange_manager_bitmex = ExchangeManager(config, "bitmex")
        await exchange_manager_bitmex.initialize()
        Exchanges.instance().add_exchange(exchange_manager_bitmex, "")

        exchange_manager_poloniex = ExchangeManager(config, "poloniex")
        await exchange_manager_poloniex.initialize()
        Exchanges.instance().add_exchange(exchange_manager_poloniex, "")

        exchanges = Exchanges.instance().get_all_exchanges()
        assert exchanges[0].exchange_manager is exchange_manager_binance
        assert exchanges[1].exchange_manager is exchange_manager_bitmex
        assert exchanges[2].exchange_manager is exchange_manager_poloniex

        await exchange_manager_binance.stop()
        await exchange_manager_bitmex.stop()
        await exchange_manager_poloniex.stop()
