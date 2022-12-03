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

from tests import event_loop
from octobot_commons.tests.test_config import load_test_config
from octobot_commons.constants import CONFIG_CRYPTO_CURRENCIES
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.api.exchange import cancel_ccxt_throttle_task

pytestmark = pytest.mark.asyncio


class TestExchangeConfig:
    EXCHANGE_NAME = "binanceus"

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
            "Avalanche": {
                "pairs": ["AVAX/BTC"]
            },
            "Ethereum": {
                "enabled": True,
                "pairs": ["ETH/USDT"]
            },
            "Uniswap": {
                "enabled": False,
                "pairs": ["UNI/BTC"]
            }
        }

        _, exchange_manager = await self.init_default(config=config)

        assert exchange_manager.exchange_config.traded_cryptocurrencies == {
            "Ethereum": ["ETH/USDT"],
            "Avalanche": ["AVAX/BTC"]
        }
        all_pairs = sorted(["AVAX/BTC", "ETH/USDT", "UNI/BTC"])
        all_enabled_pairs = sorted(["AVAX/BTC", "ETH/USDT"])
        assert sorted(exchange_manager.exchange_config.traded_symbol_pairs) == all_enabled_pairs
        assert sorted(exchange_manager.exchange_config.all_config_symbol_pairs) == all_pairs
        cancel_ccxt_throttle_task()
        await exchange_manager.stop()

    async def test_traded_pairs_with_wildcard(self):
        config = load_test_config()
        config[CONFIG_CRYPTO_CURRENCIES] = {
            "Bitcoin": {
                "pairs": ["*"],
                "quote": "BTC"
            },
            "Ethereum": {
                "enabled": False,
                "pairs": ["*"],
                "quote": "ETH"
            }
        }
        _, exchange_manager = await self.init_default(config=config)

        assert "UNI/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "AVAX/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "ADA/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "MATIC/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "ONT/BTC" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "BTC/USDT" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "ETH/USDT" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "AVAX/BNB" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "ETH/BTC" in exchange_manager.exchange_config.traded_symbol_pairs
        assert "ETH/BTC" in exchange_manager.exchange_config.all_config_symbol_pairs

        # disabled
        assert "Ethereum" not in exchange_manager.exchange_config.traded_cryptocurrencies
        assert "ADA/ETH" not in exchange_manager.exchange_config.traded_symbol_pairs

        cancel_ccxt_throttle_task()
        await exchange_manager.stop()

    async def test_traded_pairs_with_invalid_wildcard(self):
        config = load_test_config()

        # missing quote key
        config[CONFIG_CRYPTO_CURRENCIES] = {
            "Bitcoin": {
                "enabled": True,
                "pairs": ["*"],
                "quote": "BTC"
            },
            "Ethereum": {
                "pairs": ["*"],
            }
        }
        _, exchange_manager = await self.init_default(config=config)

        assert "TRX/BTC" in exchange_manager.exchange_config.traded_symbol_pairs
        assert "ADA/BTC" in exchange_manager.exchange_config.traded_symbol_pairs
        assert "BNB/BTC" in exchange_manager.exchange_config.all_config_symbol_pairs
        assert "ADA/BTC" in exchange_manager.exchange_config.all_config_symbol_pairs
        assert "Bitcoin" in exchange_manager.exchange_config.traded_cryptocurrencies

        # invalid ETH wildcard config
        assert "Ethereum" not in exchange_manager.exchange_config.traded_cryptocurrencies

        cancel_ccxt_throttle_task()
        await exchange_manager.stop()

    async def test_traded_pairs_with_add(self):
        config = load_test_config()
        config[CONFIG_CRYPTO_CURRENCIES] = {
            "Bitcoin": {
                "pairs": ["*"],
                "quote": "BTC",
                "add": ["BTC/USDT"]
            },
            "Ethereum": {
                "enabled": False,
                "pairs": ["*"],
                "quote": "ETH",
                "add": ["ETH/USDT"]
            }
        }

        _, exchange_manager = await self.init_default(config=config)

        assert "UNI/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "AVAX/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "ADA/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "MATIC/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "LINK/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "ONT/BTC" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "BTC/USDT" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "ETH/USDT" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "AVAX/BNB" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "BTC/USDT" in exchange_manager.exchange_config.traded_symbol_pairs
        assert "BTC/USDT" in exchange_manager.exchange_config.all_config_symbol_pairs

        # disabled
        assert "Ethereum" not in exchange_manager.exchange_config.traded_cryptocurrencies
        assert "ADA/ETH" not in exchange_manager.exchange_config.traded_symbol_pairs
        assert "ETH/USDT" not in exchange_manager.exchange_config.traded_symbol_pairs
        assert "ETH/USDT" in exchange_manager.exchange_config.all_config_symbol_pairs
        cancel_ccxt_throttle_task()
        await exchange_manager.stop()

    async def test_traded_pairs_with_redundancy(self):
        config = load_test_config()
        config[CONFIG_CRYPTO_CURRENCIES] = {
            "Binance Coin": {
                "pairs": [
                    "BNB/USDT"
                ]
            },
            "Binance USD": {
                "pairs": [
                    "BNB/BUSD"
                ]
            },
            "Bitcoin": {
                "enabled": True,
                "pairs": [
                    "BNB/BTC"
                ]
            },
            "Tether": {
                "enabled": True,
                "pairs": [
                    "BNB/USDT"
                ]
            }
        }

        _, exchange_manager = await self.init_default(config=config)

        assert exchange_manager.exchange_config.traded_cryptocurrencies["Binance Coin"] == ["BNB/USDT"]
        assert exchange_manager.exchange_config.traded_cryptocurrencies["Binance USD"] == ["BNB/BUSD"]
        assert exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"] == ["BNB/BTC"]
        assert exchange_manager.exchange_config.traded_cryptocurrencies["Tether"] == ["BNB/USDT"]

        sorted_pairs_without_redundancy = sorted(["BNB/USDT", "BNB/BUSD", "BNB/BTC"])
        assert sorted(exchange_manager.exchange_config.traded_symbol_pairs) == sorted_pairs_without_redundancy
        assert sorted(exchange_manager.exchange_config.all_config_symbol_pairs) == sorted_pairs_without_redundancy

        cancel_ccxt_throttle_task()
        await exchange_manager.stop()
