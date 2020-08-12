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
from octobot_trading.orders.states.order_state_factory import create_order_state
from tests import event_loop
from tests.exchanges import simulated_trader, simulated_exchange_manager
from tests.orders import buy_limit_order

import pytest

pytestmark = pytest.mark.asyncio


async def test_create_order_state_open(buy_limit_order):
    buy_limit_order.status = OrderStatus.OPEN
    await create_order_state(buy_limit_order)
    assert buy_limit_order.state.state is OrderStates.OPEN


async def test_create_order_state_cancel(buy_limit_order):
    buy_limit_order.status = OrderStatus.CANCELED
    await create_order_state(buy_limit_order)
    assert buy_limit_order.state.state is OrderStates.CLOSED  # (should be OrderStates.FILLED), but instant closed


async def test_create_order_state_fill(buy_limit_order):
    buy_limit_order.status = OrderStatus.FILLED
    await create_order_state(buy_limit_order)
    assert buy_limit_order.state.state is OrderStates.CLOSED  # (should be OrderStates.FILLED), but instant closed


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
    assert buy_limit_order.state.state is OrderStates.CLOSED  # (should be OrderStates.CANCELLED), but instant closed


async def test_create_order_state_cancel_to_open_with_ignore(buy_limit_order):
    buy_limit_order.status = OrderStatus.CANCELED
    await create_order_state(buy_limit_order)
    buy_limit_order.status = OrderStatus.OPEN
    await create_order_state(buy_limit_order, ignore_states=[OrderStates.OPEN])
    assert buy_limit_order.state.state is OrderStates.CLOSED  # currently instant closed
