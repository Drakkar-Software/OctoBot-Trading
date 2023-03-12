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

import pytest
from octobot_commons.tests.test_config import load_test_config

from tests import event_loop
import octobot_trading.personal_data as personal_data
from octobot_trading.enums import TradeOrderSide, TradeOrderType, TraderOrderType
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.exchanges.traders.trader_simulator import TraderSimulator
from octobot_trading.api.exchange import cancel_ccxt_throttle_task

pytestmark = pytest.mark.asyncio


class TestOrderFactory:
    DEFAULT_SYMBOL = "BTC/USDT"
    EXCHANGE_MANAGER_CLASS_STRING = "binanceus"

    @staticmethod
    async def init_default():
        config = load_test_config()
        exchange_manager = ExchangeManager(config, TestOrderFactory.EXCHANGE_MANAGER_CLASS_STRING)
        await exchange_manager.initialize()

        trader = TraderSimulator(config, exchange_manager)
        await trader.initialize()

        return config, exchange_manager, trader

    @staticmethod
    async def stop(exchange_manager):
        cancel_ccxt_throttle_task()
        await exchange_manager.stop()

    async def test_parse_order_type(self):
        _, exchange_manager, trader_inst = await self.init_default()

        order_to_test = personal_data.Order(trader_inst)
        assert order_to_test.simulated is True

        ccxt_order_buy_market = {
            "side": TradeOrderSide.BUY,
            "type": TradeOrderType.MARKET
        }

        order_to_test.update_from_raw(ccxt_order_buy_market)
        assert order_to_test.order_type == TraderOrderType.BUY_MARKET

        ccxt_order_buy_limit = {
            "side": TradeOrderSide.BUY,
            "type": TradeOrderType.LIMIT
        }
        assert personal_data.parse_order_type(ccxt_order_buy_limit) == (TradeOrderSide.BUY, TraderOrderType.BUY_LIMIT)

        ccxt_order_sell_market = {
            "side": TradeOrderSide.SELL,
            "type": TradeOrderType.MARKET
        }
        assert personal_data.parse_order_type(ccxt_order_sell_market) == (TradeOrderSide.SELL, TraderOrderType.SELL_MARKET)

        ccxt_order_sell_limit = {
            "side": TradeOrderSide.SELL,
            "type": TradeOrderType.LIMIT
        }
        assert personal_data.parse_order_type(ccxt_order_sell_limit) == (TradeOrderSide.SELL, TraderOrderType.SELL_LIMIT)

        await self.stop(exchange_manager)

    async def test_create_order_from_dict(self):
        price = decimal.Decimal("100")
        quantity = decimal.Decimal("2")
        _, exchange_manager, trader_inst = await self.init_default()
        limit_order = personal_data.create_order_instance(
            trader_inst,
            TraderOrderType.SELL_LIMIT,
            self.DEFAULT_SYMBOL,
            price,
            quantity,
            price=price,
            order_id="123",
            tag="tag",
            reduce_only=True,
            exchange_creation_params={"plop": 1, "fake_param": True},
            associated_entry_id="1",
        )
        order_dict = limit_order.to_dict()
        created_from_dict = personal_data.create_order_from_dict(trader_inst, order_dict)
        assert created_from_dict.origin_price == limit_order.origin_price == price
        assert created_from_dict.origin_quantity == limit_order.origin_quantity == quantity
        assert created_from_dict.__class__ is limit_order.__class__ == personal_data.SellLimitOrder
        assert created_from_dict.symbol == limit_order.symbol == self.DEFAULT_SYMBOL
        assert created_from_dict.order_id == limit_order.order_id == "123"
        assert created_from_dict.tag == limit_order.tag == "tag"
        assert created_from_dict.reduce_only is limit_order.reduce_only is True
        # exchange_creation_params are not copied
        assert created_from_dict.exchange_creation_params == {}
        assert limit_order.exchange_creation_params == {"plop": 1, "fake_param": True}
        # associated_entry_ids are not copied
        assert created_from_dict.associated_entry_ids is None
        assert limit_order.associated_entry_ids == ["1"]
