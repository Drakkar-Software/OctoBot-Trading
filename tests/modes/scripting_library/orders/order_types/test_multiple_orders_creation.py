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
import asyncio
import pytest
import mock
import decimal
import contextlib

import octobot_commons.constants as commons_constants
import octobot_trading.personal_data as trading_personal_data
import octobot_trading.personal_data.orders.order_util as order_util
import octobot_trading.modes.scripting_library as scripting_library
import octobot_trading.api as api
import octobot_trading.errors as errors
import octobot_trading.constants as trading_constants

from tests import event_loop
from tests.modes.scripting_library import mock_context
from tests.exchanges import backtesting_trader, backtesting_config, backtesting_exchange_manager, fake_backtesting
import tests.personal_data.portfolios as portfolios
import tests.test_utils.order_util as test_order_util


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("backtesting_config", ["USDT"], indirect=["backtesting_config"])
async def test_orders_with_invalid_values(mock_context):
    initial_usdt_holdings, btc_price = await _usdt_trading_context(mock_context)

    with mock.patch.object(trading_personal_data, "get_up_to_date_price", mock.AsyncMock(return_value=btc_price)), \
         mock.patch.object(order_util, "get_up_to_date_price", mock.AsyncMock(return_value=btc_price)), \
         mock.patch.object(mock_context.trader, "create_order", mock.AsyncMock()) as create_order_mock:

        with pytest.raises(errors.InvalidArgumentError):
            # no amount
            await scripting_library.market(
                mock_context,
                side="buy"
            )
            create_order_mock.assert_not_called()
            create_order_mock.reset_mock()

        with pytest.raises(errors.InvalidArgumentError):
            # negative amount
            await scripting_library.market(
                mock_context,
                amount="-1",
                side="buy"
            )
            create_order_mock.assert_not_called()
            create_order_mock.reset_mock()

        with pytest.raises(errors.InvalidArgumentError):
            # missing offset parameter
            await scripting_library.limit(
                mock_context,
                target_position="20%",
                side="buy"
            )

        with pytest.raises(errors.InvalidArgumentError):
            # missing side parameter
            await scripting_library.market(
                mock_context,
                amount="1"
            )

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
async def test_orders_amount_then_position_sequence(mock_context):
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
        await _fill_and_check(mock_context, btc_val, usdt_val, orders)

        # buy for 10% of the portfolio available value
        orders = await scripting_library.limit(
            mock_context,
            amount="10%a",
            offset="0",
            side="buy"
        )
        btc_val = btc_val + decimal.Decimal(str((45000 * decimal.Decimal("0.1")) / 500))    # 19.0
        usdt_val = usdt_val * decimal.Decimal(str(0.9))     # 40500.00
        await _fill_and_check(mock_context, btc_val, usdt_val, orders)

        # buy for for 10% of the current position value
        orders = await scripting_library.market(
            mock_context,
            amount="10%p",
            side="buy"
        )
        usdt_val = usdt_val - (btc_val * decimal.Decimal("0.1") * btc_price)   # 39550.00
        btc_val = btc_val * decimal.Decimal("1.1")   # 20.90
        await _fill_and_check(mock_context, btc_val, usdt_val, orders)

    # price changes to 1000
    btc_price = 1000
    mock_context.exchange_manager.exchange_personal_data.portfolio_manager.handle_mark_price_update(
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
        await _fill_and_check(mock_context, btc_val, usdt_val, orders)

        # buy to reach a target position of 60% of the total portfolio (in BTC)
        orders = await scripting_library.limit(
            mock_context,
            target_position="60%",
            offset=0
        )
        previous_btc_val = btc_val
        btc_val = (btc_val + (usdt_val / btc_price)) * decimal.Decimal("0.6")   # 36.27
        usdt_val = usdt_val - (btc_val - previous_btc_val) * btc_price   # 24180.00
        await _fill_and_check(mock_context, btc_val, usdt_val, orders)

        # buy to reach a target position including an additional 50% of the available USDT in BTC
        orders = await scripting_library.market(
            mock_context,
            target_position="50%a"
        )
        btc_val = btc_val + usdt_val / 2 / btc_price   # 48.36
        usdt_val = usdt_val / 2   # 12090.00
        await _fill_and_check(mock_context, btc_val, usdt_val, orders)

        # sell to keep only 10% of the position, sell at 2000 (1000 + 100%)
        orders = await scripting_library.limit(
            mock_context,
            target_position="10%p",
            offset="100%"
        )
        usdt_val = usdt_val + btc_val * decimal.Decimal("0.9") * (btc_price * 2)  # 99138.00
        btc_val = btc_val / 10   # 4.836
        await _fill_and_check(mock_context, btc_val, usdt_val, orders)


@pytest.mark.parametrize("backtesting_config", ["USDT"], indirect=["backtesting_config"])
async def test_concurrent_orders(mock_context):
    async with _20_percent_position_trading_context(mock_context) as context_data:
        btc_val, usdt_val, btc_price = context_data

        # create 3 sell orders (at price = 500 + 10 = 510)
        # that would end up selling more than what we have if not executed sequentially
        # 1st order is 80% of position, second is 80% of the remaining 20% and so on

        orders = []
        async def create_order(amount):
            orders.append(
                (await scripting_library.limit(
                    mock_context,
                    amount=amount,
                    offset=10,
                    side="sell"
                ))[0]
            )
        await asyncio.gather(
            *(
                create_order("80%p")
                for _ in range(3)
            )
        )

        initial_btc_holdings = btc_val
        btc_val = initial_btc_holdings * decimal.Decimal("0.2") ** 3  # 0.16
        usdt_val = usdt_val + (initial_btc_holdings - btc_val) * (btc_price + 10)   # 50118.40
        await _fill_and_check(mock_context, btc_val, usdt_val, orders, orders_count=3)

        # create 3 buy orders (at price = 500 + 10 = 510) all of them for a target position of 10%
        # first order gets created to have this 10% position, others are also created like this, ending up in a 30%
        # position

        # update portfolio current value
        mock_context.exchange_manager.exchange_personal_data.portfolio_manager.handle_balance_updated()

        orders = []

        async def create_order(target_position):
            orders.append(
                (await scripting_library.limit(
                    mock_context,
                    target_position=target_position,
                    offset=10
                ))[0]
            )
        await asyncio.gather(
            *(
                create_order("10%")
                for _ in range(3)
            )
        )

        initial_btc_holdings = btc_val  # 0.16
        initial_total_val = initial_btc_holdings * btc_price + usdt_val
        initial_position_percent = decimal.Decimal(initial_btc_holdings * btc_price / initial_total_val)
        btc_val = initial_btc_holdings + \
                  initial_total_val * (decimal.Decimal("0.1") - initial_position_percent) * 3 / btc_price    # 29.79904
        usdt_val = usdt_val - (btc_val - initial_btc_holdings) * (btc_price + 10)   # 35002.4896
        await _fill_and_check(mock_context, btc_val, usdt_val, orders, orders_count=3)


@pytest.mark.parametrize("backtesting_config", ["USDT"], indirect=["backtesting_config"])
async def test_sell_limit_with_stop_loss_orders_single_sell_and_stop_with_linked_to(mock_context):
    async with _20_percent_position_trading_context(mock_context) as context_data:
        btc_val, usdt_val, btc_price = context_data

        sell_limit_orders = await scripting_library.limit(
            mock_context,
            target_position="0%",
            offset=50,
        )
        stop_loss_orders = await scripting_library.stop_loss(
            mock_context,
            target_position="0%",
            offset=-75,
            linked_to=sell_limit_orders
        )
        assert len(sell_limit_orders) == len(stop_loss_orders) == 1

        # stop order is filled
        usdt_val = usdt_val + btc_val * (btc_price - 75)   # 48500.00
        btc_val = trading_constants.ZERO    # 0.00
        await _fill_and_check(mock_context, btc_val, usdt_val, stop_loss_orders, logged_orders_count=2)
        # linked order is cancelled
        assert sell_limit_orders[0].is_cancelled()


@pytest.mark.parametrize("backtesting_config", ["USDT"], indirect=["backtesting_config"])
async def test_sell_limit_with_stop_loss_orders_two_sells_and_stop_with_oco(mock_context):
    async with _20_percent_position_trading_context(mock_context) as context_data:
        btc_val, usdt_val, btc_price = context_data

        stop_loss_orders = await scripting_library.stop_loss(
            mock_context,
            target_position="0%",
            offset=-50,
            side="sell",
            one_cancels_the_other=True,
            tag="exitPosition"
        )
        take_profit_limit_orders_1 = await scripting_library.limit(
            mock_context,
            target_position="50%p",
            offset=50
        )
        take_profit_limit_orders_2 = await scripting_library.limit(
            mock_context,
            target_position="0%p",
            offset=100,
            one_cancels_the_other=True,
            tag="exitPosition"
        )

        # take_profit_limit_orders_1 filled
        available_btc_val = trading_constants.ZERO  # 10.00
        total_btc_val = btc_val / 2  # 10.00
        usdt_val = usdt_val + btc_val / 2 * (btc_price + 50)   # 40000.00
        await _fill_and_check(mock_context, available_btc_val, usdt_val, take_profit_limit_orders_1,
                              btc_total=total_btc_val)
        # linked order is not cancelled
        assert stop_loss_orders[0].is_open()

        # take_profit_limit_orders_2 filled
        usdt_val = usdt_val + btc_val / 2 * (btc_price + 100)   # 40000.00
        btc_val = trading_constants.ZERO  # 0.00
        await _fill_and_check(mock_context, btc_val, usdt_val, take_profit_limit_orders_2)
        # linked order is cancelled
        assert stop_loss_orders[0].is_cancelled()


async def _usdt_trading_context(mock_context):
    initial_usdt_holdings = 50000
    mock_context.exchange_manager.exchange_personal_data.portfolio_manager.portfolio.update_portfolio_from_balance({
        'BTC': {'available': decimal.Decimal(0), 'total': decimal.Decimal(0)},
        'ETH': {'available': decimal.Decimal(0), 'total': decimal.Decimal(0)},
        'USDT': {'available': decimal.Decimal(str(initial_usdt_holdings)),
                 'total': decimal.Decimal(str(initial_usdt_holdings))}
    }, mock_context.exchange_manager)
    mock_context.exchange_manager.exchange_personal_data.portfolio_manager.handle_balance_updated()
    btc_price = 500
    mock_context.exchange_manager.exchange_personal_data.portfolio_manager.handle_mark_price_update(
        "BTC/USDT", btc_price)
    return initial_usdt_holdings, btc_price


@contextlib.asynccontextmanager
async def _20_percent_position_trading_context(mock_context):
    initial_usdt_holdings, btc_price = await _usdt_trading_context(mock_context)
    usdt_val = decimal.Decimal(str(initial_usdt_holdings))
    with mock.patch.object(trading_personal_data, "get_up_to_date_price", mock.AsyncMock(return_value=btc_price)), \
            mock.patch.object(order_util, "get_up_to_date_price", mock.AsyncMock(return_value=btc_price)):
        # initial limit buy order: buy with 20% of portfolio
        buy_limit_orders = await scripting_library.limit(
            mock_context,
            target_position="20%",
            offset=0,
            side="buy"
        )
        btc_val = (usdt_val * decimal.Decimal("0.2")) / btc_price  # 20.00
        usdt_val = usdt_val * decimal.Decimal("0.8")  # 40000.00
        await _fill_and_check(mock_context, btc_val, usdt_val, buy_limit_orders)
        yield btc_val, usdt_val, btc_price


async def _fill_and_check(mock_context, btc_available, usdt_available, orders,
                          btc_total=None, usdt_total=None, orders_count=1, logged_orders_count=None):
    for order in orders:
        if isinstance(order, trading_personal_data.LimitOrder):
            await test_order_util.fill_limit_or_stop_order(order)
        elif isinstance(order, trading_personal_data.MarketOrder):
            await test_order_util.fill_market_order(order)

    _ensure_orders_validity(mock_context, btc_available, usdt_available, orders,
                            btc_total=btc_total, usdt_total=usdt_total, orders_count=orders_count,
                            logged_orders_count=logged_orders_count)


def _ensure_orders_validity(mock_context, btc_available, usdt_available, orders,
                            btc_total=None, usdt_total=None, orders_count=1, logged_orders_count=None):
    exchange_manager = mock_context.exchange_manager
    btc_total = btc_total or btc_available
    usdt_total = usdt_total or usdt_available
    assert len(orders) == orders_count
    assert all(isinstance(order, trading_personal_data.Order) for order in orders)
    assert mock_context.orders_writer.log_many.call_count == logged_orders_count or orders_count
    mock_context.orders_writer.log_many.reset_mock()
    mock_context.logger.warning.assert_not_called()
    mock_context.logger.warning.reset_mock()
    mock_context.logger.exception.assert_not_called()
    mock_context.logger.exception.reset_mock()
    assert api.get_portfolio_currency(exchange_manager, "BTC").available == btc_available
    assert api.get_portfolio_currency(exchange_manager, "BTC").total == btc_total
    assert api.get_portfolio_currency(exchange_manager, "USDT").available == usdt_available
    assert api.get_portfolio_currency(exchange_manager, "USDT").total == usdt_total
