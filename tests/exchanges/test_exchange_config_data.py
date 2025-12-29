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
import mock

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

        await exchange_manager.initialize(exchange_config_by_exchange=None)
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

        assert "AVAX/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "ADA/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "MATIC/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "ONT/BTC" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "BTC/USDT" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "ETH/USDT" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "AVAX/BNB" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "ETH/BTC" in exchange_manager.exchange_config.traded_symbol_pairs

        # inactive markets
        assert "UNI/BTC" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]

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

        assert "ADA/BTC" in exchange_manager.exchange_config.traded_symbol_pairs
        assert "Bitcoin" in exchange_manager.exchange_config.traded_cryptocurrencies

        # inactive markets
        assert "TRX/BTC" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]

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

        assert "AVAX/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "ADA/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "MATIC/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "LINK/BTC" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "ONT/BTC" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "BTC/USDT" in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "ETH/USDT" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "AVAX/BNB" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]
        assert "BTC/USDT" in exchange_manager.exchange_config.traded_symbol_pairs

        # inactive markets
        assert "UNI/BTC" not in exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"]

        # disabled
        assert "Ethereum" not in exchange_manager.exchange_config.traded_cryptocurrencies
        assert "ADA/ETH" not in exchange_manager.exchange_config.traded_symbol_pairs
        assert "ETH/USDT" not in exchange_manager.exchange_config.traded_symbol_pairs
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
        assert exchange_manager.exchange_config.traded_cryptocurrencies["Bitcoin"] == ["BNB/BTC"]
        assert exchange_manager.exchange_config.traded_cryptocurrencies["Tether"] == ["BNB/USDT"]

        # inactive markets
        assert exchange_manager.exchange_config.traded_cryptocurrencies["Binance USD"] == []

        sorted_pairs_without_redundancy = sorted(["BNB/USDT", "BNB/BTC"])
        assert sorted(exchange_manager.exchange_config.traded_symbol_pairs) == sorted_pairs_without_redundancy

        cancel_ccxt_throttle_task()
        await exchange_manager.stop()

    @pytest.mark.parametrize("watch_only,added_pairs,removed_pairs", [
        (False, ["ADA/USDT"], []),
        (True, ["ETH/USDT"], []),
        (False, ["ADA/USDT", "LINK/USDT"], []),
        (False, [], ["BTC/USDT"]),
        (True, [], ["BTC/USDT"]),
    ])
    async def test_update_traded_symbol_pairs(self, watch_only, added_pairs, removed_pairs):
        config = load_test_config()
        config[CONFIG_CRYPTO_CURRENCIES] = {
            "Bitcoin": {
                "pairs": ["BTC/USDT"]
            }
        }
        _, exchange_manager = await self.init_default(config=config)
        
        # Pre-populate lists for removal tests
        if removed_pairs:
            for pair in removed_pairs:
                if pair not in exchange_manager.exchange_config.traded_symbol_pairs:
                    exchange_manager.exchange_config.traded_symbol_pairs.append(pair)
            if watch_only:
                exchange_manager.exchange_config.additional_traded_pairs = removed_pairs.copy()
                exchange_manager.exchange_config.watched_pairs = removed_pairs.copy()
            else:
                exchange_manager.exchange_config.additional_traded_pairs = removed_pairs.copy()
        
        with mock.patch.object(exchange_manager.exchange_config, '_is_valid_symbol', wraps=exchange_manager.exchange_config._is_valid_symbol) as is_valid_mock:
            await exchange_manager.exchange_config.update_traded_symbol_pairs(
                added_pairs=added_pairs,
                removed_pairs=removed_pairs,
                watch_only=watch_only
            )
            
            # Verify _is_valid_symbol was called for all pairs
            assert is_valid_mock.call_count == len(added_pairs) + len(removed_pairs)
        
        if watch_only:
            for pair in added_pairs:
                assert pair in exchange_manager.exchange_config.watched_pairs
            for pair in removed_pairs:
                assert pair not in exchange_manager.exchange_config.watched_pairs
        else:
            for pair in added_pairs:
                assert pair in exchange_manager.exchange_config.additional_traded_pairs
            for pair in removed_pairs:
                assert pair not in exchange_manager.exchange_config.additional_traded_pairs
        
        cancel_ccxt_throttle_task()
        await exchange_manager.stop()
