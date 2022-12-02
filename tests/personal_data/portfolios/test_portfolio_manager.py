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
import os

import pytest
from mock import patch, Mock, AsyncMock
from octobot_trading.personal_data.orders import BuyMarketOrder, BuyLimitOrder

from tests.exchanges import backtesting_trader, backtesting_config, backtesting_exchange_manager, fake_backtesting
from tests import event_loop

# All test coroutines will be treated as marked.
from tests.personal_data import DEFAULT_MARKET_QUANTITY
from tests.test_utils.random_numbers import decimal_random_price, decimal_random_quantity

pytestmark = pytest.mark.asyncio


async def test_handle_balance_update(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager

    if os.getenv('CYTHON_IGNORE'):
        return

    with patch.object(portfolio_manager.portfolio, 'update_portfolio_from_balance',
                      new=Mock()) as update_portfolio_from_balance_mock:
        update_portfolio_from_balance_mock.assert_not_called()

        portfolio_manager.handle_balance_update(None)
        update_portfolio_from_balance_mock.assert_not_called()

        trader.is_enabled = False
        portfolio_manager.handle_balance_update({})
        update_portfolio_from_balance_mock.assert_not_called()

        trader.is_enabled = True
        portfolio_manager.handle_balance_update({})
        update_portfolio_from_balance_mock.assert_called_once()


async def test_handle_balance_update_from_order(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager

    trader.simulate = False
    order = BuyMarketOrder(trader)

    if os.getenv('CYTHON_IGNORE'):
        return

    with patch.object(portfolio_manager, '_refresh_real_trader_portfolio',
                      new=AsyncMock()) as _refresh_real_trader_portfolio_mock, \
        patch.object(portfolio_manager, '_refresh_simulated_trader_portfolio_from_order',
                     new=Mock()) as _refresh_simulated_trader_portfolio_from_order_mock:
        _refresh_real_trader_portfolio_mock.assert_not_called()
        await portfolio_manager.handle_balance_update_from_order(order, True)
        _refresh_real_trader_portfolio_mock.assert_called_once()
        _refresh_simulated_trader_portfolio_from_order_mock.assert_not_called()
        _refresh_real_trader_portfolio_mock.reset_mock()
        await portfolio_manager.handle_balance_update_from_order(order, False)
        _refresh_real_trader_portfolio_mock.assert_not_called()
        _refresh_simulated_trader_portfolio_from_order_mock.assert_called_once()

    trader.simulate = True
    with patch.object(portfolio_manager, '_refresh_simulated_trader_portfolio_from_order',
                      new=Mock()) as _refresh_simulated_trader_portfolio_from_order_mock:
        _refresh_simulated_trader_portfolio_from_order_mock.assert_not_called()
        await portfolio_manager.handle_balance_update_from_order(order, True)
        _refresh_simulated_trader_portfolio_from_order_mock.assert_called_once()
        _refresh_simulated_trader_portfolio_from_order_mock.reset_mock()
        # ensure no side effect with require_exchange_update param
        await portfolio_manager.handle_balance_update_from_order(order, False)
        _refresh_simulated_trader_portfolio_from_order_mock.assert_called_once()

    trader.is_enabled = False
    trader.simulate = False
    assert not await portfolio_manager.handle_balance_update_from_order(order, True)
    assert not await portfolio_manager.handle_balance_update_from_order(order, False)


async def test_refresh_simulated_trader_portfolio_from_order(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager

    if os.getenv('CYTHON_IGNORE'):
        return
    order = BuyLimitOrder(trader)
    await order.initialize()
    with patch.object(portfolio_manager.portfolio, 'update_portfolio_available',
                      new=Mock()) as update_portfolio_available_mock:
        update_portfolio_available_mock.assert_not_called()
        portfolio_manager._refresh_simulated_trader_portfolio_from_order(order)
        update_portfolio_available_mock.assert_called_once()

    price = decimal_random_price()
    order.update(
        price=decimal_random_price(),
        quantity=decimal_random_quantity(max_value=DEFAULT_MARKET_QUANTITY / price),
        symbol="BTC/USDT"
    )
    await order.on_fill(force_fill=True)
    assert order.is_filled()

    with patch.object(portfolio_manager.portfolio, 'update_portfolio_from_filled_order',
                      new=Mock()) as update_portfolio_from_filled_order_mock:
        update_portfolio_from_filled_order_mock.assert_not_called()
        portfolio_manager._refresh_simulated_trader_portfolio_from_order(order)
        update_portfolio_from_filled_order_mock.assert_called_once()
