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
from octobot_commons.constants import CONFIG_CRYPTO_CURRENCIES
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.api.exchange import cancel_ccxt_throttle_task

pytestmark = pytest.mark.asyncio


class TestExchangeConfig:
    EXCHANGE_NAME = "binance"

    @staticmethod
    async def init_default(config=None):
        if not config:
            config = load_test_config()

        exchange_manager = ExchangeManager(config, TestExchangeConfig.EXCHANGE_NAME)

        await exchange_manager.initialize()
        return config, exchange_manager

    async def test_traded_pairs(self):
        config = load_test_config()
        config[CONFIG_CRYPTO_CURRENCIES] = {
            "Neo": {
                "pairs": ["NEO/BTC"]
            },
            "Ethereum": {
                "pairs": ["ETH/USDT"]
            },
            "Icon": {
                "pairs": ["ICX/BTC"]
            }
        }

        _, exchange_manager = await self.init_default(config=config)

        assert exchange_manager.exchange_config.traded_cryptocurrencies == {
            "Ethereum": ["ETH/USDT"],
            "Icon": ["ICX/BTC"],
            "Neo": ["NEO/BTC"]
        }
        cancel_ccxt_throttle_task()
        await exchange_manager.stop()

    async def test_traded_pairs_with_wildcard(self):
        config = load_test_config()
        config[CONFIG_CRYPTO_CURRENCIES] = {
            "Bitcoin": {
                "pairs": "*",
                "quote": "BTC"
            }
        }
        _, exchange_manager = await self.init_default(config=config)

        assert "ICX/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "NEO/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "VEN/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "XLM/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "ONT/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "BTC/USDT" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "ETH/USDT" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "NEO/BNB" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        cancel_ccxt_throttle_task()
        await exchange_manager.stop()

    async def test_traded_pairs_with_add(self):
        config = load_test_config()
        config[CONFIG_CRYPTO_CURRENCIES] = {
            "Bitcoin": {
                "pairs": "*",
                "quote": "BTC",
                "add": ["BTC/USDT"]
            }
        }

        _, exchange_manager = await self.init_default(config=config)

        assert "ICX/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "NEO/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "VEN/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "XLM/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "ONT/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "BTC/USDT" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "ETH/USDT" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "NEO/BNB" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        cancel_ccxt_throttle_task()
        await exchange_manager.stop()
