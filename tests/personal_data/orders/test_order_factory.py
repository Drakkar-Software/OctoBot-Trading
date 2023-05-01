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
import octobot_trading.storage.orders_storage as orders_storage
from octobot_trading.enums import TradeOrderSide, TradeOrderType, TraderOrderType, StoredOrdersAttr
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
        await self.stop(exchange_manager)

    async def test_create_order_from_order_storage_details_with_simple_order(self):
        _, exchange_manager, trader_inst = await self.init_default()    
        
        order = personal_data.BuyLimitOrder(trader_inst)
        order.update(order_type=TraderOrderType.BUY_LIMIT,
                     symbol="BTC/USDT",
                     current_price=decimal.Decimal("70"),
                     quantity=decimal.Decimal("10"),
                     price=decimal.Decimal("70"))
        order_storage_details = orders_storage._format_order(order, exchange_manager)
        order_storage_details[StoredOrdersAttr.ENTRIES.value] = ["11111"]
    
        pending_groups = {}
        created_order = await personal_data.create_order_from_order_storage_details(
            order_storage_details, exchange_manager, pending_groups
        )
        assert pending_groups == {}
    
        assert created_order.exchange_manager is exchange_manager
        assert created_order.origin_quantity == order.origin_quantity
        assert created_order.origin_price == order.origin_price
        assert created_order.__class__ is order.__class__
        # associated_entry_ids are added from order_storage_details but not in original order
        assert created_order.associated_entry_ids == ["11111"]
        assert order.associated_entry_ids is None
        await self.stop(exchange_manager)
    
    async def test_create_order_from_order_storage_details_with_groups(self):
        _, exchange_manager, trader_inst = await self.init_default()  
        
        order = personal_data.BuyLimitOrder(trader_inst)
        group = exchange_manager.exchange_personal_data.orders_manager.create_group(
            personal_data.OneCancelsTheOtherOrderGroup
        )
        order.update(order_type=TraderOrderType.BUY_LIMIT,
                     symbol="BTC/USDT",
                     current_price=decimal.Decimal("70"),
                     quantity=decimal.Decimal("10"),
                     price=decimal.Decimal("70"),
                     group=group)
        order_storage_details = orders_storage._format_order(order, exchange_manager)
    
        pending_groups = {}
        created_order = await personal_data.create_order_from_order_storage_details(
            order_storage_details, exchange_manager, pending_groups
        )
        assert created_order.order_group is group
        assert pending_groups == {group.name: group}
        await self.stop(exchange_manager)

    async def test_create_order_from_order_storage_details_with_chained_orders_with_group(self):
        _, exchange_manager, trader_inst = await self.init_default()
    
        order = personal_data.BuyLimitOrder(trader_inst)
        group_1 = exchange_manager.exchange_personal_data.orders_manager.create_group(
            personal_data.OneCancelsTheOtherOrderGroup
        )
        group_2 = exchange_manager.exchange_personal_data.orders_manager.create_group(
            personal_data.OneCancelsTheOtherOrderGroup
        )
        chained_order_1 = personal_data.BuyLimitOrder(trader_inst)
        chained_order_2 = personal_data.SellLimitOrder(trader_inst)
        chained_order_3 = personal_data.SellLimitOrder(trader_inst)
        for to_update_order in (order, chained_order_1, chained_order_2, chained_order_3):
            to_update_order.update(
                order_type=TraderOrderType.BUY_LIMIT,
                symbol="BTC/USDT",
                current_price=decimal.Decimal("70"),
                quantity=decimal.Decimal("10"),
                price=decimal.Decimal("70")
            )
        chained_order_1.add_to_order_group(group_1)
        chained_order_2.add_to_order_group(group_1)
        chained_order_3.add_to_order_group(group_2)
        await chained_order_1.set_as_chained_order(order, False, {}, False)
        await chained_order_2.set_as_chained_order(order, True, {"plop_1": True, "plop_2": {"hi": 1}}, False)
        order.add_chained_order(chained_order_1)
        order.add_chained_order(chained_order_2)
        await chained_order_3.set_as_chained_order(chained_order_1, False, {}, False)
        chained_order_1.add_chained_order(chained_order_3)
        order_storage_details = orders_storage._format_order(order, exchange_manager)
    
        pending_groups = {}
        created_order = await personal_data.create_order_from_order_storage_details(
            order_storage_details, exchange_manager, pending_groups
        )
        assert pending_groups == {
            group_1.name: group_1,
            group_2.name: group_2,
        }
        chained_orders = created_order.chained_orders
        assert len(chained_orders) == 2
        for chained_order in chained_orders:
            assert chained_order.order_group is group_1
    
        assert chained_orders[0].triggered_by is created_order
        assert chained_orders[0].has_been_bundled is False
        assert chained_orders[0].exchange_creation_params == {}
        assert chained_orders[1].triggered_by is created_order
        assert chained_orders[1].has_been_bundled is True
        assert chained_orders[1].exchange_creation_params == {"plop_1": True, "plop_2": {"hi": 1}}
        assert chained_orders[1].chained_orders == []
        second_level_chained_orders = chained_orders[0].chained_orders
        assert len(second_level_chained_orders) == 1
        assert second_level_chained_orders[0].order_group is group_2
        assert second_level_chained_orders[0].chained_orders == []
        assert second_level_chained_orders[0].triggered_by is chained_orders[0]
        assert second_level_chained_orders[0].has_been_bundled is False
        assert second_level_chained_orders[0].exchange_creation_params == {}
        await self.stop(exchange_manager)
