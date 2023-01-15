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
import typing
import pytest
from octobot_commons.tests.test_config import load_test_config
from octobot_trading.personal_data.orders.orders_manager import OrdersManager
from octobot_trading.enums import (
    OrderStatus,
)
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.exchanges.traders.trader_simulator import TraderSimulator
from octobot_trading.api.exchange import cancel_ccxt_throttle_task

pytestmark = pytest.mark.asyncio


class TestOrdersManager:
    DEFAULT_SYMBOL = "BTC/USDT"
    EXCHANGE_MANAGER_CLASS_STRING = "binanceus"
    first_time = 1631111111.0
    second_time = 1631111112.0
    third_time = 1631111113.0
    fourth_time = 1631111114.0
    raw_orders = [
        {
            "id": "1",
            "timestamp": first_time,
            "symbol": DEFAULT_SYMBOL,
            "type": "market",
            "timeInForce": "GTC",
            "postOnly": False,
            "side": "buy",
            "price": 50,
            "stopPrice": None,
            "amount": 5.4,
            "cost": None,
            "average": None,
            "filled": 0,
            "remaining": 5.4,
            "status": "closed",
            "fee": {"cost": 0.03764836, "currency": "USDT"},
        },
        {
            "id": "2",
            "timestamp": second_time,
            "symbol": DEFAULT_SYMBOL,
            "type": "limit",
            "timeInForce": "GTC",
            "postOnly": False,
            "side": "buy",
            "price": 50,
            "stopPrice": None,
            "amount": 5.4,
            "cost": None,
            "average": None,
            "filled": 0.0,
            "remaining": 5.4,
            "status": "open",
            "fee": {"cost": 0.03764836, "currency": "USDT"},
        },
        {
            "id": "3",
            "timestamp": third_time,
            "symbol": DEFAULT_SYMBOL,
            "type": "limit",
            "timeInForce": "GTC",
            "postOnly": False,
            "side": "buy",
            "price": 60,
            "stopPrice": None,
            "amount": 5.4,
            "cost": None,
            "average": None,
            "filled": 0.0,
            "remaining": 5.4,
            "status": "open",
            "fee": {"cost": 0.03764836, "currency": "USDT"},
            "tag": "test",
        },
        {
            "id": "4",
            "timestamp": fourth_time,
            "symbol": DEFAULT_SYMBOL,
            "type": "limit",
            "timeInForce": "GTC",
            "postOnly": False,
            "side": "buy",
            "price": 70,
            "stopPrice": None,
            "amount": 5.4,
            "cost": None,
            "average": None,
            "filled": 5.4,
            "remaining": 0.0,
            "status": "open",
            "fee": {"cost": 0.03764836, "currency": "USDT"},
            "tag": "test",
        },
    ]

    @staticmethod
    async def init_default() -> typing.Tuple[OrdersManager, ExchangeManager]:
        config = load_test_config()
        exchange_manager = ExchangeManager(
            config, TestOrdersManager.EXCHANGE_MANAGER_CLASS_STRING
        )
        await exchange_manager.initialize()

        trader = TraderSimulator(config, exchange_manager)
        await trader.initialize()
        orders_manager = OrdersManager(trader)
        return orders_manager, exchange_manager

    @staticmethod
    async def stop(exchange_manager):
        cancel_ccxt_throttle_task()
        await exchange_manager.stop()

    async def reset_orders_manager(self, orders_manager, status=None):
        orders_manager.initialize_impl()
        await upsert_raw_orders(self.raw_orders, orders_manager, status)

    async def test_get_order(self):
        orders_manager, exchange_manager = await self.init_default()
        await self.reset_orders_manager(orders_manager)
        order = orders_manager.get_order("2")
        assert order.order_id == "2"
        self.stop(exchange_manager)

    async def test_get_all_orders(self):
        orders_manager, exchange_manager = await self.init_default()
        await self.reset_orders_manager(orders_manager)
        one_order = orders_manager.get_all_orders(
            symbol=self.DEFAULT_SYMBOL,
            since=self.second_time,
            until=self.third_time,
            limit=1,
            tag=None,
        )
        assert len(one_order) == 1
        assert one_order[0].order_id == "2"

        two_orders = orders_manager.get_all_orders(
            symbol=self.DEFAULT_SYMBOL,
            since=self.second_time,
            until=self.third_time,
            limit=-1,
            tag=None,
        )
        assert len(two_orders) == 2
        assert two_orders[0].order_id == "2"
        assert two_orders[1].order_id == "3"

        since_orders = orders_manager.get_all_orders(
            symbol=self.DEFAULT_SYMBOL,
            since=self.second_time,
            until=-1,
            limit=-1,
            tag=None,
        )
        assert len(since_orders) == 3
        assert since_orders[0].order_id == "2"
        assert since_orders[1].order_id == "3"
        assert since_orders[2].order_id == "4"

        until_orders = orders_manager.get_all_orders(
            symbol=self.DEFAULT_SYMBOL,
            since=-1,
            until=self.third_time,
            limit=-1,
            tag=None,
        )
        assert len(until_orders) == 3
        assert until_orders[0].order_id == "1"
        assert until_orders[1].order_id == "2"
        assert until_orders[2].order_id == "3"

        all_orders = orders_manager.get_all_orders(
            symbol=self.DEFAULT_SYMBOL, since=-1, until=-1, limit=-1, tag=None
        )
        assert len(all_orders) == 4
        assert all_orders[0].order_id == "1"
        assert all_orders[1].order_id == "2"
        assert all_orders[2].order_id == "3"
        assert all_orders[3].order_id == "4"

        # TODO uncomment once tags are parsed
        # tagged_order = orders_manager.get_all_orders(
        #     symbol=self.DEFAULT_SYMBOL, since=-1, until=-1, limit=-1, tag="test"
        # )
        # assert len(tagged_order) == 1
        # assert tagged_order[0].order_id == "4"
        self.stop(exchange_manager)

    async def test_get_pending_cancel_orders(self):
        orders_manager, exchange_manager = await self.init_default()
        await self.reset_orders_manager(
            orders_manager, OrderStatus.PENDING_CANCEL.value
        )
        one_order = orders_manager.get_pending_cancel_orders(
            symbol=self.DEFAULT_SYMBOL,
            since=self.second_time,
            until=self.third_time,
            limit=1,
            tag=None,
        )
        assert len(one_order) == 1
        assert one_order[0].order_id == "2"

        two_orders = orders_manager.get_pending_cancel_orders(
            symbol=self.DEFAULT_SYMBOL,
            since=self.second_time,
            until=self.third_time,
            limit=-1,
            tag=None,
        )
        assert len(two_orders) == 2
        assert two_orders[0].order_id == "2"
        assert two_orders[1].order_id == "3"

        since_orders = orders_manager.get_pending_cancel_orders(
            symbol=self.DEFAULT_SYMBOL,
            since=self.second_time,
            until=-1,
            limit=-1,
            tag=None,
        )
        assert len(since_orders) == 3
        assert since_orders[0].order_id == "2"
        assert since_orders[1].order_id == "3"
        assert since_orders[2].order_id == "4"

        until_orders = orders_manager.get_pending_cancel_orders(
            symbol=self.DEFAULT_SYMBOL,
            since=-1,
            until=self.third_time,
            limit=-1,
            tag=None,
        )
        assert len(until_orders) == 3
        assert until_orders[0].order_id == "1"
        assert until_orders[1].order_id == "2"
        assert until_orders[2].order_id == "3"

        all_orders = orders_manager.get_pending_cancel_orders(
            symbol=self.DEFAULT_SYMBOL, since=-1, until=-1, limit=-1, tag=None
        )
        assert len(all_orders) == 4
        assert all_orders[0].order_id == "1"
        assert all_orders[1].order_id == "2"
        assert all_orders[2].order_id == "3"
        assert all_orders[3].order_id == "4"

        # TODO uncomment once tags are parsed
        # tagged_order = orders_manager.get_pending_cancel_orders(
        #     symbol=self.DEFAULT_SYMBOL, since=-1, until=-1, limit=-1, tag="test"
        # )
        # assert len(tagged_order) == 1
        # assert tagged_order[0].order_id == "4"
        self.stop(exchange_manager)

    async def test_get_closed_orders(self):
        orders_manager, exchange_manager = await self.init_default()
        await self.reset_orders_manager(orders_manager, OrderStatus.CLOSED.value)
        one_order = orders_manager.get_closed_orders(
            symbol=self.DEFAULT_SYMBOL,
            since=self.second_time,
            until=self.third_time,
            limit=1,
            tag=None,
        )
        assert len(one_order) == 1
        assert one_order[0].order_id == "2"

        two_orders = orders_manager.get_closed_orders(
            symbol=self.DEFAULT_SYMBOL,
            since=self.second_time,
            until=self.third_time,
            limit=-1,
            tag=None,
        )
        assert len(two_orders) == 2
        assert two_orders[0].order_id == "2"
        assert two_orders[1].order_id == "3"

        since_orders = orders_manager.get_closed_orders(
            symbol=self.DEFAULT_SYMBOL,
            since=self.second_time,
            until=-1,
            limit=-1,
            tag=None,
        )
        assert len(since_orders) == 3
        assert since_orders[0].order_id == "2"
        assert since_orders[1].order_id == "3"
        assert since_orders[2].order_id == "4"

        until_orders = orders_manager.get_closed_orders(
            symbol=self.DEFAULT_SYMBOL,
            since=-1,
            until=self.third_time,
            limit=-1,
            tag=None,
        )
        assert len(until_orders) == 3
        assert until_orders[0].order_id == "1"
        assert until_orders[1].order_id == "2"
        assert until_orders[2].order_id == "3"

        all_orders = orders_manager.get_closed_orders(
            symbol=self.DEFAULT_SYMBOL, since=-1, until=-1, limit=-1, tag=None
        )
        assert len(all_orders) == 4
        assert all_orders[0].order_id == "1"
        assert all_orders[1].order_id == "2"
        assert all_orders[2].order_id == "3"
        assert all_orders[3].order_id == "4"

        # TODO uncomment once tags are parsed
        # tagged_order = orders_manager.get_closed_orders(
        #     symbol=self.DEFAULT_SYMBOL, since=-1, until=-1, limit=-1, tag="test"
        # )
        # assert len(tagged_order) == 1
        # assert tagged_order[0].order_id == "4"

        self.stop(exchange_manager)

    async def test_get_open_orders(self):
        orders_manager, exchange_manager = await self.init_default()
        await self.reset_orders_manager(orders_manager, OrderStatus.OPEN.value)
        one_order = orders_manager.get_open_orders(
            symbol=self.DEFAULT_SYMBOL,
            since=self.second_time,
            until=self.third_time,
            limit=1,
            tag=None,
        )
        assert len(one_order) == 1
        assert one_order[0].order_id == "2"

        two_orders = orders_manager.get_open_orders(
            symbol=self.DEFAULT_SYMBOL,
            since=self.second_time,
            until=self.third_time,
            limit=-1,
            tag=None,
        )
        assert len(two_orders) == 2
        assert two_orders[0].order_id == "2"
        assert two_orders[1].order_id == "3"

        since_orders = orders_manager.get_open_orders(
            symbol=self.DEFAULT_SYMBOL,
            since=self.second_time,
            until=-1,
            limit=-1,
            tag=None,
        )
        assert len(since_orders) == 3
        assert since_orders[0].order_id == "2"
        assert since_orders[1].order_id == "3"
        assert since_orders[2].order_id == "4"

        until_orders = orders_manager.get_open_orders(
            symbol=self.DEFAULT_SYMBOL,
            since=-1,
            until=self.third_time,
            limit=-1,
            tag=None,
        )
        assert len(until_orders) == 3
        assert until_orders[0].order_id == "1"
        assert until_orders[1].order_id == "2"
        assert until_orders[2].order_id == "3"

        all_orders = orders_manager.get_open_orders(
            symbol=self.DEFAULT_SYMBOL, since=-1, until=-1, limit=-1, tag=None
        )
        assert len(all_orders) == 4
        assert all_orders[0].order_id == "1"
        assert all_orders[1].order_id == "2"
        assert all_orders[2].order_id == "3"
        assert all_orders[3].order_id == "4"

        # TODO uncomment once tags are parsed
        # tagged_order = orders_manager.get_open_orders(
        #     symbol=self.DEFAULT_SYMBOL, since=-1, until=-1, limit=-1, tag="test"
        # )
        # assert len(tagged_order) == 1
        # assert tagged_order[0].order_id == "4"

        self.stop(exchange_manager)


async def upsert_raw_orders(raw_orders, orders_manager: OrdersManager, status=None):
    for order in raw_orders:
        order = {**order}
        order["status"] = status or order["status"]
        await orders_manager.upsert_order_from_raw(order["id"], order, False)
