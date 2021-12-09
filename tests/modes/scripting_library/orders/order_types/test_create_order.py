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

import octobot_trading.personal_data as trading_personal_data
import octobot_trading.modes.scripting_library.orders.order_types.create_order as create_order
import octobot_trading.modes.scripting_library.orders.position_size as position_size
import octobot_trading.modes.scripting_library.orders.offsets as offsets
import octobot_trading.modes.scripting_library.data as library_data
import octobot_trading.enums as trading_enums
import octobot_trading.errors as errors
import octobot_trading.constants as trading_constants

from tests import event_loop
from tests.modes.scripting_library import null_context, mock_context, symbol_market
from tests.exchanges import backtesting_trader, backtesting_config, backtesting_exchange_manager, fake_backtesting


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_create_order_instance(mock_context):
    with mock.patch.object(create_order, "_get_order_quantity_and_side",
                           mock.AsyncMock(return_value=(decimal.Decimal(1), "sell"))) \
            as _get_order_quantity_and_side_mock, \
            mock.patch.object(create_order, "_get_order_details",
                              mock.AsyncMock(return_value=(1, 2, 3, 4, 5, 6, 7, 8, 9))) \
            as _get_order_details_mock, \
            mock.patch.object(create_order, "_create_order", mock.AsyncMock()) as _create_order_mock:
        await create_order.create_order_instance(
            mock_context, "side", "symbol", "order_amount", "order_target_position",
            "order_type_name", "order_offset")  # todo add other params
        _get_order_quantity_and_side_mock.assert_called_once_with(mock_context, "order_amount",
                                                                  "order_target_position", "order_type_name", "side")
        _get_order_details_mock.assert_called_once_with(mock_context, "order_type_name", "sell", "order_offset", False,
                                                        None)
        _create_order_mock.assert_called_once_with(mock_context, "symbol", decimal.Decimal(1), 2, None,
                                                   1, 3, None, 7, None)


def test_use_total_holding():
    assert create_order._use_total_holding("") is False
    assert create_order._use_total_holding("market") is False
    assert create_order._use_total_holding("limit") is False
    assert create_order._use_total_holding("stop_loss") is True
    assert create_order._use_total_holding("stop_market") is True
    assert create_order._use_total_holding("stop_limit") is True
    assert create_order._use_total_holding("trailing_stop_loss") is True
    assert create_order._use_total_holding("trailing_market") is False
    assert create_order._use_total_holding("trailing_limit") is False


async def test_get_order_quantity_and_side(null_context):
    # order_amount and order_target_position are both not set
    with pytest.raises(errors.InvalidArgumentError):
        await create_order._get_order_quantity_and_side(null_context, None, None, "", "")

    # order_amount and order_target_position are set
    with pytest.raises(errors.InvalidArgumentError):
        await create_order._get_order_quantity_and_side(null_context, 1, 2, "", "")

    # order_amount but no side
    with pytest.raises(errors.InvalidArgumentError):
        await create_order._get_order_quantity_and_side(null_context, 1, None, "", None)
    with pytest.raises(errors.InvalidArgumentError):
        await create_order._get_order_quantity_and_side(null_context, 1, None, "", "fsdsfds")

    with mock.patch.object(position_size, "get_amount",
                           mock.AsyncMock(return_value=decimal.Decimal(1))) as get_amount_mock:
        with mock.patch.object(create_order, "_use_total_holding",
                               mock.Mock(return_value=False)) as _use_total_holding_mock:
            assert await create_order._get_order_quantity_and_side(null_context, 1, None, "", "sell") \
                   == (decimal.Decimal(1), "sell")
            get_amount_mock.assert_called_once_with(null_context, 1, "sell", use_total_holding=False)
            get_amount_mock.reset_mock()
            _use_total_holding_mock.assert_called_once_with("")
        with mock.patch.object(create_order, "_use_total_holding",
                               mock.Mock(return_value=True)) as _use_total_holding_mock:
            assert await create_order._get_order_quantity_and_side(null_context, 1, None, "order_type", "sell") \
                   == (decimal.Decimal(1), "sell")
            get_amount_mock.assert_called_once_with(null_context, 1, "sell", use_total_holding=True)
            get_amount_mock.reset_mock()
            _use_total_holding_mock.assert_called_once_with("order_type")

    with mock.patch.object(position_size, "get_target_position",
                           mock.AsyncMock(return_value=(decimal.Decimal(10), "buy"))) as get_target_position_mock:
        with mock.patch.object(create_order, "_use_total_holding",
                               mock.Mock(return_value=True)) as _use_total_holding_mock:
            assert await create_order._get_order_quantity_and_side(null_context, None, 1, "order_type", None) \
                   == (decimal.Decimal(10), "buy")
            get_target_position_mock.assert_called_once_with(null_context, 1, use_total_holding=True)
            get_target_position_mock.reset_mock()
            _use_total_holding_mock.assert_called_once_with("order_type")
        with mock.patch.object(create_order, "_use_total_holding",
                               mock.Mock(return_value=False)) as _use_total_holding_mock:
            assert await create_order._get_order_quantity_and_side(null_context, None, 1, "order_type", None) \
                   == (decimal.Decimal(10), "buy")
            get_target_position_mock.assert_called_once_with(null_context, 1, use_total_holding=False)
            get_target_position_mock.reset_mock()
            _use_total_holding_mock.assert_called_once_with("order_type")


async def test_get_order_details(null_context):
    ten = decimal.Decimal(10)
    with mock.patch.object(offsets, "get_offset", mock.AsyncMock(return_value=ten)) as get_offset_mock:

        async def _test_market(side, expected_order_type):
            order_type, order_price, side, _, _, _, _, _, _ = await create_order._get_order_details(
                null_context, "market", side, None, None, None
            )
            assert order_type is expected_order_type
            assert order_price == ten
            assert side is None
            get_offset_mock.assert_called_once_with(null_context, "0")
            get_offset_mock.reset_mock()
        await _test_market(trading_enums.TradeOrderSide.SELL.value, trading_enums.TraderOrderType.SELL_MARKET)
        await _test_market(trading_enums.TradeOrderSide.BUY.value, trading_enums.TraderOrderType.BUY_MARKET)

        async def _test_limit(side, expected_order_type):
            order_type, order_price, side, _, _, _, _, _, _ = await create_order._get_order_details(
                null_context, "limit", side, "25%", None, None
            )
            assert order_type is expected_order_type
            assert order_price == ten
            assert side is None
            get_offset_mock.assert_called_once_with(null_context, "25%")
            get_offset_mock.reset_mock()
        await _test_limit(trading_enums.TradeOrderSide.SELL.value, trading_enums.TraderOrderType.SELL_LIMIT)
        await _test_limit(trading_enums.TradeOrderSide.BUY.value, trading_enums.TraderOrderType.BUY_LIMIT)

        async def _test_stop_loss(side, expected_side):
            order_type, order_price, side, _, _, _, _, _, _ = await create_order._get_order_details(
                null_context, "stop_loss", side, "25%", None, None
            )
            assert order_type is trading_enums.TraderOrderType.STOP_LOSS
            assert order_price == ten
            assert side is expected_side
            get_offset_mock.assert_called_once_with(null_context, "25%")
            get_offset_mock.reset_mock()
        await _test_stop_loss(trading_enums.TradeOrderSide.SELL.value, trading_enums.TradeOrderSide.SELL)
        await _test_stop_loss(trading_enums.TradeOrderSide.BUY.value, trading_enums.TradeOrderSide.BUY)

        async def _test_trailing_market(side, expected_side):
            order_type, order_price, side, _, trailing_method, _, _, _, _ = await create_order._get_order_details(
                null_context, "trailing_market", side, "25%", None, None
            )
            assert order_type is trading_enums.TraderOrderType.TRAILING_STOP
            assert trailing_method == "continuous"
            assert order_price == ten
            assert side is expected_side
            get_offset_mock.assert_called_once_with(null_context, "25%")
            get_offset_mock.reset_mock()
        await _test_trailing_market(trading_enums.TradeOrderSide.SELL.value, trading_enums.TradeOrderSide.SELL)
        await _test_trailing_market(trading_enums.TradeOrderSide.BUY.value, trading_enums.TradeOrderSide.BUY)

        async def _test_trailing_limit(side, expected_side):
            order_type, order_price, side, _, trailing_method, min_offset_val, max_offset_val, _, _ \
                = await create_order._get_order_details(
                null_context, "trailing_limit", side, "25%", None, None
            )
            assert order_type is trading_enums.TraderOrderType.TRAILING_STOP_LIMIT
            assert trailing_method == "continuous"
            assert order_price is None
            assert side is expected_side
            assert min_offset_val == ten
            assert max_offset_val == ten
            assert get_offset_mock.call_count == 2
            get_offset_mock.reset_mock()
        await _test_trailing_limit(trading_enums.TradeOrderSide.SELL.value, trading_enums.TradeOrderSide.SELL)
        await _test_trailing_limit(trading_enums.TradeOrderSide.BUY.value, trading_enums.TradeOrderSide.BUY)


async def test_create_order(mock_context, symbol_market):
    with mock.patch.object(trading_personal_data, "get_pre_order_data",
                           mock.AsyncMock(return_value=(None, None, None, decimal.Decimal(105), symbol_market))) \
        as get_pre_order_data_mock, \
        mock.patch.object(library_data, "store_orders", mock.AsyncMock()) as store_orders_mock:
        await create_order._create_order(mock_context, "BTC/USDT", decimal.Decimal(1), decimal.Decimal(100), None,
                                         trading_enums.TraderOrderType.BUY_MARKET, None, None, None,
                                         None)
        get_pre_order_data_mock.assert_called_once_with(mock_context.exchange_manager, symbol="BTC/USDT",
                                                        timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT)
        store_orders_mock.assert_called_once()
        assert store_orders_mock.mock_calls
        assert store_orders_mock.mock_calls[0].args[0] is mock_context
        orders = store_orders_mock.mock_calls[0].args[1]
        assert len(orders) == 1
        assert isinstance(orders[0], trading_personal_data.BuyMarketOrder)
        assert orders[0].symbol == "BTC/USDT"
        assert orders[0].origin_price == decimal.Decimal(105)
        assert orders[0].origin_quantity == decimal.Decimal(1)
        get_pre_order_data_mock.reset_mock()
        store_orders_mock.reset_mock()

        await create_order._create_order(mock_context, "BTC/USDT", decimal.Decimal(1), decimal.Decimal(100), None,
                                         trading_enums.TraderOrderType.TRAILING_STOP,
                                         trading_enums.TradeOrderSide.BUY, decimal.Decimal(5), None,
                                         [trading_personal_data.LimitOrder(mock_context.trader)])
        get_pre_order_data_mock.assert_called_once_with(mock_context.exchange_manager, symbol="BTC/USDT",
                                                        timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT)
        store_orders_mock.assert_called_once()
        assert store_orders_mock.mock_calls
        assert store_orders_mock.mock_calls[0].args[0] is mock_context
        orders = store_orders_mock.mock_calls[0].args[1]
        assert len(orders) == 1
        assert isinstance(orders[0], trading_personal_data.TrailingStopOrder)
        assert orders[0].symbol == "BTC/USDT"
        assert orders[0].origin_price == decimal.Decimal(100)
        assert orders[0].origin_quantity == decimal.Decimal(1)
        assert orders[0].trader == mock_context.trader
        assert orders[0].trailing_percent == decimal.Decimal(5)
