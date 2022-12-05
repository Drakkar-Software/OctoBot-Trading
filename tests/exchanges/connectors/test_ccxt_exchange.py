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
import decimal

import ccxt.async_support
from mock import patch, Mock

import octobot_trading.exchanges.connectors as exchange_connectors
import octobot_trading.enums as enums
import octobot_trading.exchange_data.contracts as contracts
import pytest

from tests.exchanges import exchange_manager, future_simulated_exchange_manager, set_future_exchange_fees
from tests.exchanges.traders import future_trader, future_trader_simulator_with_default_linear, DEFAULT_FUTURE_SYMBOL, \
    DEFAULT_FUTURE_SYMBOL_MARGIN_TYPE, DEFAULT_FUTURE_SYMBOL_LEVERAGE

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

    with patch.object(ccxt_exchange, 'client', new=MockCCXT()):
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

    with patch.object(ccxt_exchange, 'client', new=MockCCXT()):
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

    with patch.object(ccxt_exchange, 'client', new=MockCCXT()):
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


async def test_get_trade_fee(exchange_manager, future_trader_simulator_with_default_linear):
    spot_fees_value = 0.001
    future_symbol = "BTC/USDT:USDT"
    future_fees_value = 0.0004
    spot_symbol = "BTC/USDT"
    config, fut_exchange_manager_inst, trader_inst, default_contract = future_trader_simulator_with_default_linear
    fut_exchange_manager_inst.is_future = True
    fut_ccxt_exchange = exchange_connectors.CCXTExchange(config, fut_exchange_manager_inst)
    spot_ccxt_exchange = exchange_connectors.CCXTExchange(exchange_manager.config, exchange_manager)

    # spot trading
    spot_ccxt_exchange.client.options['defaultType'] = enums.ExchangeTypes.SPOT.value
    await spot_ccxt_exchange.client.load_markets()
    assert spot_fees_value / 5 <= spot_ccxt_exchange.client.markets[spot_symbol]['taker'] <= spot_fees_value * 5
    assert spot_ccxt_exchange.get_trade_fee(spot_symbol, enums.TraderOrderType.BUY_LIMIT, decimal.Decimal("0.45"),
                                            decimal.Decimal(10000), "taker") == \
           _get_fees("taker", "BTC", 0.001, decimal.Decimal("0.00045"))
    assert spot_ccxt_exchange.get_trade_fee(spot_symbol, enums.TraderOrderType.SELL_LIMIT, decimal.Decimal("0.45"),
                                            decimal.Decimal(10000), "maker") == \
           _get_fees("maker", "USDT", 0.001, decimal.Decimal("4.5"))

    # future trading
    fut_ccxt_exchange.client.options['defaultType'] = enums.ExchangeTypes.FUTURE.value
    await fut_ccxt_exchange.client.load_markets()
    # enforce taker and maker values
    set_future_exchange_fees(fut_ccxt_exchange, future_symbol, taker=future_fees_value, maker=future_fees_value)
    assert future_fees_value / 5 <= fut_ccxt_exchange.client.markets[future_symbol]['taker'] <= future_fees_value * 5
    # linear
    assert fut_ccxt_exchange.get_trade_fee(future_symbol, enums.TraderOrderType.BUY_LIMIT, decimal.Decimal("0.45"),
                                           decimal.Decimal(10000), "taker") == \
           _get_fees("taker", "USDT", future_fees_value, decimal.Decimal("1.800000"))
    # inverse
    fut_ccxt_exchange.client.markets[future_symbol]["inverse"] = True
    fut_ccxt_exchange.client.markets[future_symbol]["linear"] = False
    contract = contracts.FutureContract(pair=future_symbol,
                                        margin_type=enums.MarginType.ISOLATED,
                                        contract_type=enums.FutureContractType.INVERSE_PERPETUAL)
    fut_exchange_manager_inst.exchange.pair_contracts[future_symbol] = contract
    assert fut_ccxt_exchange.get_trade_fee(future_symbol, enums.TraderOrderType.BUY_LIMIT, decimal.Decimal("0.45"),
                                           decimal.Decimal(10000), "taker") == \
           _get_fees("taker", "BTC", future_fees_value, decimal.Decimal("0.00018"))


def _get_fees(type, currency, rate, cost):
    return {
        enums.FeePropertyColumns.TYPE.value: type,
        enums.FeePropertyColumns.CURRENCY.value: currency,
        enums.FeePropertyColumns.RATE.value: rate,
        enums.FeePropertyColumns.COST.value: decimal.Decimal(str(cost)),
    }
