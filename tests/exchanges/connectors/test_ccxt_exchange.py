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
import mock

import octobot_trading.exchanges.connectors as exchange_connectors
import octobot_trading.enums as enums
import pytest

from tests.exchanges import exchange_manager

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_initialize_impl_with_none_symbols_and_timeframes(exchange_manager):
    ccxt_exchange = exchange_connectors.CCXTExchange(exchange_manager.config, exchange_manager)

    class MockCCXT:
        def __init__(self):
            self.symbols = None
            self.timeframes = None

        async def load_markets(self):
            pass

        def setSandboxMode(self, is_sandboxed):
            pass

    with mock.patch.object(ccxt_exchange, 'client', new=MockCCXT()):
        await ccxt_exchange.initialize_impl()
        assert ccxt_exchange.symbols == set()
        assert ccxt_exchange.time_frames == set()


async def test_initialize_impl_with_empty_symbols_and_timeframes(exchange_manager):
    ccxt_exchange = exchange_connectors.CCXTExchange(exchange_manager.config, exchange_manager)

    class MockCCXT:
        def __init__(self):
            self.symbols = []
            self.timeframes = []

        async def load_markets(self):
            pass

        def setSandboxMode(self, is_sandboxed):
            pass

    with mock.patch.object(ccxt_exchange, 'client', new=MockCCXT()):
        await ccxt_exchange.initialize_impl()
        assert ccxt_exchange.symbols == set()
        assert ccxt_exchange.time_frames == set()


async def test_initialize_impl(exchange_manager):
    ccxt_exchange = exchange_connectors.CCXTExchange(exchange_manager.config, exchange_manager)

    class MockCCXT:
        def __init__(self):
            self.symbols = [
                "BTC/USDT",
                "ETH/USDT",
                "ETH/BTC",
                "ETH/USDT"
            ]
            self.timeframes = [
                "1h",
                "2h",
                "4h",
                "2h"
            ]

        async def load_markets(self):
            pass

        def setSandboxMode(self, is_sandboxed):
            pass

    with mock.patch.object(ccxt_exchange, 'client', new=MockCCXT()):
        await ccxt_exchange.initialize_impl()
        assert ccxt_exchange.symbols == {
                "BTC/USDT",
                "ETH/USDT",
                "ETH/BTC",
        }
        assert ccxt_exchange.time_frames == {
            "1h",
            "2h",
            "4h",
        }


async def test_set_symbol_partial_take_profit_stop_loss(exchange_manager):
    ccxt_exchange = exchange_connectors.CCXTExchange(exchange_manager.config, exchange_manager)
    with pytest.raises(NotImplementedError):
        await ccxt_exchange.set_symbol_partial_take_profit_stop_loss("BTC/USDT", False,
                                                                     enums.TakeProfitStopLossMode.PARTIAL)


async def test_get_ccxt_order_type(exchange_manager):
    ccxt_exchange = exchange_connectors.CCXTExchange(exchange_manager.config, exchange_manager)
    with pytest.raises(RuntimeError):
        ccxt_exchange.get_ccxt_order_type(None)
    with pytest.raises(RuntimeError):
        ccxt_exchange.get_ccxt_order_type(enums.TraderOrderType.UNKNOWN)
    assert ccxt_exchange.get_ccxt_order_type(enums.TraderOrderType.BUY_LIMIT) == enums.TradeOrderType.LIMIT.value
    assert ccxt_exchange.get_ccxt_order_type(enums.TraderOrderType.STOP_LOSS_LIMIT) == enums.TradeOrderType.LIMIT.value
    assert ccxt_exchange.get_ccxt_order_type(enums.TraderOrderType.TRAILING_STOP) == enums.TradeOrderType.MARKET.value
    assert ccxt_exchange.get_ccxt_order_type(enums.TraderOrderType.SELL_MARKET) == enums.TradeOrderType.MARKET.value
