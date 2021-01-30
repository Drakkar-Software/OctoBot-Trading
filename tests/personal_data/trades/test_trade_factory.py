#  Drakkar-Software OctoBot
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
import json
import time

import pytest

from tests import event_loop
from octobot_commons.tests.test_config import load_test_config
from octobot_trading.enums import TraderOrderType, OrderStatus
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.personal_data.orders.order_factory import create_order_instance_from_raw
from octobot_trading.exchanges.traders.trader_simulator import TraderSimulator

from octobot_trading.personal_data.trades import create_trade_instance_from_raw, create_trade_from_order, \
    create_trade_instance

# All test coroutines will be treated as marked.
from octobot_trading.api.exchange import cancel_ccxt_throttle_task

pytestmark = pytest.mark.asyncio


class TestTradeFactory:
    DEFAULT_SYMBOL = "BTC/USDT"
    EXCHANGE_MANAGER_CLASS_STRING = "binance"

    @staticmethod
    async def init_default():
        config = load_test_config()
        exchange_manager = ExchangeManager(config, TestTradeFactory.EXCHANGE_MANAGER_CLASS_STRING)
        await exchange_manager.initialize()

        trader = TraderSimulator(config, exchange_manager)
        await trader.initialize()

        return config, exchange_manager, trader

    @staticmethod
    async def stop(exchange_manager):
        cancel_ccxt_throttle_task()
        await exchange_manager.stop()

    async def test_create_trade_instance_from_raw(self):
        _, exchange_manager, trader = await self.init_default()

        raw_trade = json.loads(
            """
            {	
              "info": {},
              "id": "12345-67890:09876/54321",
              "timestamp": 1502962946216,
              "datetime": "2017-08-17 12:42:48.000",
              "symbol": "ETH/BTC",
              "order": "12345-67890:09876/54321",
              "type": "limit",
              "side": "buy",
              "takerOrMaker": "taker",
              "price": 0.06917684,
              "amount": 1.5,
              "cost": 0.10376526,
              "fee": {
                "cost": 0.0015,
                "currency": "ETH",
                "rate": 0.002
              }
            }
            """)

        trade = create_trade_instance_from_raw(trader, raw_trade)

        assert trade.trade_id == '12345-67890:09876/54321'
        assert trade.origin_order_id == '12345-67890:09876/54321'
        assert trade.trade_type == TraderOrderType.BUY_LIMIT
        assert trade.symbol == 'ETH/BTC'
        assert trade.total_cost == 0.10376526
        assert trade.executed_quantity == 1.5
        assert trade.origin_price == 0.06917684
        assert trade.executed_price == 0.06917684
        assert trade.executed_time == 1502962946216
        assert trade.status == OrderStatus.FILLED
        assert trade.is_closing_order is True

        await self.stop(exchange_manager)

    async def test_create_trade_from_order(self):
        _, exchange_manager, trader = await self.init_default()

        raw_order = json.loads(
            """
            {
                "id":                "12345-67890:09876/54321",
                "datetime":          "2017-08-17 12:42:48.000",
                "timestamp":          1502962946216,
                "lastTradeTimestamp": 1502962956216,
                "status":     "open",
                "symbol":     "BTC/USDT",
                "type":       "limit",
                "side":       "sell",
                "price":       7684,
                "amount":      1.5,
                "filled":      1.1,
                "remaining":   0.4,
                "cost":        0.076094524,
                "trades":    [],
                "fee": {
                    "currency": "BTC",
                    "cost": 0.0009,
                    "rate": 0.002
                },
                "info": {}
            }
            """)

        order = create_order_instance_from_raw(trader, raw_order)
        trade = create_trade_from_order(order, close_status=OrderStatus.FILLED)

        assert trade.trade_id == '12345-67890:09876/54321'
        assert trade.origin_order_id == '12345-67890:09876/54321'
        assert trade.simulated is True
        assert trade.trade_type == TraderOrderType.SELL_LIMIT
        assert trade.symbol == 'BTC/USDT'
        assert trade.total_cost == 0.076094524
        assert trade.executed_quantity == 1.1
        assert trade.origin_quantity == 1.5
        assert trade.origin_price == 7684
        assert trade.executed_price == 7684
        assert trade.status == OrderStatus.FILLED
        assert trade.is_closing_order is True

        trade = create_trade_from_order(order)
        assert trade.status == OrderStatus.FILLED

        exec_time = time.time()
        trade = create_trade_from_order(order, executed_time=exec_time)
        assert trade.executed_time == exec_time

        await self.stop(exchange_manager)

    async def test_create_trade_from_partially_filled_order(self):
        _, exchange_manager, trader = await self.init_default()

        raw_order = json.loads(
            """
            {
                "id":                "12345-67890:09876/54321",
                "datetime":          "2017-08-17 12:42:48.000",
                "timestamp":          1502962946216,
                "lastTradeTimestamp": 1502962956216,
                "status":     "open",
                "symbol":     "BTC/USDT",
                "type":       "limit",
                "side":       "sell",
                "price":       7684,
                "amount":      1.5,
                "filled":      1.1,
                "remaining":   0.4,
                "cost":        0.076094524,
                "trades":    [],
                "fee": {
                    "currency": "BTC",
                    "cost": 0.0009,
                    "rate": 0.002
                },
                "info": {}
            }
            """)

        order = create_order_instance_from_raw(trader, raw_order)
        trade = create_trade_from_order(order, close_status=OrderStatus.OPEN)

        assert trade.trade_id == '12345-67890:09876/54321'
        assert trade.origin_order_id == '12345-67890:09876/54321'
        assert trade.simulated is True
        assert trade.trade_type == TraderOrderType.SELL_LIMIT
        assert trade.symbol == 'BTC/USDT'
        assert trade.total_cost == 0.076094524
        assert trade.executed_quantity == 1.1
        assert trade.origin_quantity == 1.5
        assert trade.origin_price == 7684
        assert trade.executed_price == 7684
        assert trade.status == OrderStatus.OPEN
        assert trade.is_closing_order is False

        await self.stop(exchange_manager)

    async def test_create_trade_instance(self):
        _, exchange_manager, trader = await self.init_default()

        trade = create_trade_instance(trader,
                                      order_type=TraderOrderType.SELL_MARKET,
                                      symbol="ETH/USDT",
                                      quantity_filled=1.2,
                                      total_cost=10)

        assert trade.trade_id is not None

        assert trade.symbol == "ETH/USDT"
        assert trade.trade_type == TraderOrderType.SELL_MARKET
        assert round(trade.executed_quantity, 3) == 1.2
        assert trade.total_cost == 10

        await self.stop(exchange_manager)
