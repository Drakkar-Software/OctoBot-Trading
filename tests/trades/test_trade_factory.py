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

import pytest

from octobot_commons.tests.test_config import load_test_config
from octobot_trading.enums import TraderOrderType
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.traders.trader_simulator import TraderSimulator

# All test coroutines will be treated as marked.
from octobot_trading.trades.trade_factory import create_trade_instance_from_raw

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
        assert trade.trade_type == TraderOrderType.BUY_LIMIT
        assert trade.symbol == 'ETH/BTC'
        assert trade.total_cost == 0.10376526
        assert trade.executed_quantity == 1.5
        assert trade.origin_price == 0.06917684
        assert trade.executed_price == 0.06917684

        await self.stop(exchange_manager)
