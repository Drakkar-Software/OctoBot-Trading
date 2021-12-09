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
import pytest
import mock
import decimal

import octobot_commons.constants as commons_constants
import octobot_trading.personal_data as trading_personal_data
import octobot_trading.personal_data.orders.order_util as order_util
import octobot_trading.modes.scripting_library as scripting_library
import octobot_trading.api as api

from tests import event_loop
from tests.modes.scripting_library import mock_context
from tests.exchanges import backtesting_trader, backtesting_config, backtesting_exchange_manager, fake_backtesting
import tests.personal_data.portfolios as portfolios

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("backtesting_config", ["USDT"], indirect=["backtesting_config"])
async def test_orders_with_invalid_values(mock_context):
    initial_usdt_holdings, btc_price = await _usdt_trading_context(mock_context)

    with mock.patch.object(trading_personal_data, "get_up_to_date_price", mock.AsyncMock(return_value=btc_price)), \
         mock.patch.object(order_util, "get_up_to_date_price", mock.AsyncMock(return_value=btc_price)), \
         mock.patch.object(mock_context.trader, "create_order", mock.AsyncMock()) as create_order_mock:

        with pytest.raises(RuntimeError):
            # no amount
            await scripting_library.market(
                mock_context,
                side="buy"
            )
            create_order_mock.assert_not_called()
            create_order_mock.reset_mock()

        with pytest.raises(RuntimeError):
            # negative amount
            await scripting_library.market(
                mock_context,
                amount="-1",
                side="buy"
            )
            create_order_mock.assert_not_called()
            create_order_mock.reset_mock()

        # orders without having enough funds
        for amount, side in ((1, "sell"), (0.000000001, "buy")):
            await scripting_library.market(
                mock_context,
                amount=amount,
                side=side
            )
            create_order_mock.assert_not_called()
            create_order_mock.reset_mock()
            mock_context.orders_writer.log_many.assert_not_called()
            mock_context.orders_writer.log_many.reset_mock()
            mock_context.logger.warning.assert_called_once()
            mock_context.logger.warning.reset_mock()


@pytest.mark.parametrize("backtesting_config", ["USDT"], indirect=["backtesting_config"])
async def test_market_orders_amount_then_position_sequence(mock_context):
    initial_usdt_holdings, btc_price = await _usdt_trading_context(mock_context)

    with mock.patch.object(trading_personal_data, "get_up_to_date_price", mock.AsyncMock(return_value=btc_price)), \
         mock.patch.object(order_util, "get_up_to_date_price", mock.AsyncMock(return_value=btc_price)):

        # buy for 10% of the total portfolio value
        orders = await scripting_library.market(
            mock_context,
            amount="10%",
            side="buy"
        )
        btc_val = decimal.Decimal(10)   # 10.00
        usdt_val = decimal.Decimal(45000)   # 45000.00
        _ensure_orders_validity(mock_context, btc_val, usdt_val, orders)

        # buy for 10% of the portfolio available value
        orders = await scripting_library.market(
            mock_context,
            amount="10%a",
            side="buy"
        )
        btc_val = btc_val + decimal.Decimal(str((45000 * decimal.Decimal("0.1")) / 500))    # 19.0
        usdt_val = usdt_val * decimal.Decimal(str(0.9))     # 40500.00
        _ensure_orders_validity(mock_context, btc_val, usdt_val, orders)

        # buy for for 10% of the current position value
        orders = await scripting_library.market(
            mock_context,
            amount="10%p",
            side="buy"
        )
        usdt_val = usdt_val - (btc_val * decimal.Decimal("0.1") * btc_price)   # 39550.00
        btc_val = btc_val * decimal.Decimal("1.1")   # 20.90
        _ensure_orders_validity(mock_context, btc_val, usdt_val, orders)

    # price changes to 1000
    btc_price = 1000
    await mock_context.exchange_manager.exchange_personal_data.portfolio_manager.handle_mark_price_update(
        "BTC/USDT", btc_price)
    with mock.patch.object(trading_personal_data, "get_up_to_date_price", mock.AsyncMock(return_value=btc_price)), \
         mock.patch.object(order_util, "get_up_to_date_price", mock.AsyncMock(return_value=btc_price)):

        # buy to reach a target position of 25 btc
        orders = await scripting_library.market(
            mock_context,
            target_position=25
        )
        usdt_val = usdt_val - ((25 - btc_val) * btc_price)   # 35450.00
        btc_val = decimal.Decimal(25)   # 25
        _ensure_orders_validity(mock_context, btc_val, usdt_val, orders)

        # buy to reach a target position of 60% of the total portfolio (in BTC)
        orders = await scripting_library.market(
            mock_context,
            target_position="60%"
        )
        previous_btc_val = btc_val
        btc_val = (btc_val + (usdt_val / btc_price)) * decimal.Decimal("0.6")   # 36.27
        usdt_val = usdt_val - (btc_val - previous_btc_val) * btc_price   # 24180.00
        _ensure_orders_validity(mock_context, btc_val, usdt_val, orders)

        # buy to reach a target position including an additional 50% of the available USDT in BTC
        orders = await scripting_library.market(
            mock_context,
            target_position="50%a"
        )
        btc_val = btc_val + usdt_val / 2 / btc_price   # 48.36
        usdt_val = usdt_val / 2   # 12090.00
        _ensure_orders_validity(mock_context, btc_val, usdt_val, orders)

        # sell to keep only 10% of the position
        orders = await scripting_library.market(
            mock_context,
            target_position="10%p"
        )
        usdt_val = usdt_val + btc_val * decimal.Decimal("0.9") * btc_price  # 55614.00
        btc_val = btc_val / 10   # 4.836
        _ensure_orders_validity(mock_context, btc_val, usdt_val, orders)


@pytest.mark.parametrize("backtesting_config", ["USDT"], indirect=["backtesting_config"])
async def test_concurrent_orders(mock_context):
    pass


async def _usdt_trading_context(mock_context):
    initial_usdt_holdings = 50000
    portfolios.update_portfolio_balance({
        'BTC': {'available': decimal.Decimal(0), 'total': decimal.Decimal(0)},
        'ETH': {'available': decimal.Decimal(0), 'total': decimal.Decimal(0)},
        'USDT': {'available': decimal.Decimal(str(initial_usdt_holdings)),
                 'total': decimal.Decimal(str(initial_usdt_holdings))}
    }, mock_context.exchange_manager)
    await mock_context.exchange_manager.exchange_personal_data.portfolio_manager.handle_balance_updated()
    btc_price = 500
    await mock_context.exchange_manager.exchange_personal_data.portfolio_manager.handle_mark_price_update(
        "BTC/USDT", btc_price)
    return initial_usdt_holdings, btc_price


def _ensure_orders_validity(mock_context, btc_available, usdt_available, orders, btc_total=None, usdt_total=None):
    exchange_manager = mock_context.exchange_manager
    btc_total = btc_total or btc_available
    usdt_total = usdt_total or usdt_available
    assert len(orders) == 1
    assert isinstance(orders[0], trading_personal_data.Order)
    mock_context.orders_writer.log_many.assert_called_once()
    mock_context.orders_writer.log_many.reset_mock()
    mock_context.logger.warning.assert_not_called()
    mock_context.logger.warning.reset_mock()
    mock_context.logger.exception.assert_not_called()
    mock_context.logger.exception.reset_mock()
    assert api.get_portfolio_currency(exchange_manager, "BTC", commons_constants.PORTFOLIO_AVAILABLE) == btc_available
    assert api.get_portfolio_currency(exchange_manager, "BTC", commons_constants.PORTFOLIO_TOTAL) == btc_total
    assert api.get_portfolio_currency(exchange_manager, "USDT", commons_constants.PORTFOLIO_AVAILABLE) == usdt_available
    assert api.get_portfolio_currency(exchange_manager, "USDT", commons_constants.PORTFOLIO_TOTAL) == usdt_total
