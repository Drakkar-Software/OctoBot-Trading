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
from octobot_trading.enums import OrderStatus, OrderStates
from octobot_trading.personal_data.orders import create_order_state

import pytest
from tests import event_loop
from tests.exchanges import simulated_trader, simulated_exchange_manager
from tests.personal_data.orders import buy_limit_order

pytestmark = pytest.mark.asyncio


async def test_create_order_state_open(buy_limit_order):
    buy_limit_order.status = OrderStatus.OPEN
    await create_order_state(buy_limit_order)
    assert buy_limit_order.state.state is OrderStates.OPEN


async def test_create_order_state_cancel(buy_limit_order):
    buy_limit_order.status = OrderStatus.CANCELED
    await create_order_state(buy_limit_order)
    # can be CANCELED or instant CLOSED
    assert buy_limit_order.state.state in [OrderStates.FILLED, OrderStates.CLOSED]


async def test_create_order_state_fill(buy_limit_order):
    buy_limit_order.status = OrderStatus.FILLED
    await create_order_state(buy_limit_order)
    # can be FILLED or instant CLOSED
    assert buy_limit_order.state.state in [OrderStates.FILLED, OrderStates.CLOSED]


async def test_create_order_state_close(buy_limit_order):
    buy_limit_order.status = OrderStatus.CLOSED
    await create_order_state(buy_limit_order)
    assert buy_limit_order.state.state is OrderStates.CLOSED


async def test_create_order_state_fill_to_open_without_ignore(buy_limit_order):
    buy_limit_order.status = OrderStatus.FILLED
    await create_order_state(buy_limit_order)
    buy_limit_order.status = OrderStatus.OPEN
    await create_order_state(buy_limit_order, ignore_states=[])
    assert buy_limit_order.state.state is OrderStates.OPEN


async def test_create_order_state_fill_to_open_with_ignore(buy_limit_order):
    buy_limit_order.status = OrderStatus.FILLED
    await create_order_state(buy_limit_order)
    buy_limit_order.status = OrderStatus.OPEN
    await create_order_state(buy_limit_order, ignore_states=[OrderStates.OPEN])
    # can be FILLED or instant CLOSED
    assert buy_limit_order.state.state in [OrderStates.FILLED, OrderStates.CLOSED]


async def test_create_order_state_cancel_to_open_with_ignore(buy_limit_order):
    buy_limit_order.status = OrderStatus.CANCELED
    await create_order_state(buy_limit_order)
    buy_limit_order.status = OrderStatus.OPEN
    await create_order_state(buy_limit_order, ignore_states=[OrderStates.OPEN])
    # can be CANCELED or instant CLOSED
    assert buy_limit_order.state.state in [OrderStates.CANCELED, OrderStates.CLOSED]
