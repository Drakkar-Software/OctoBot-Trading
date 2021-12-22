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
import octobot_trading.modes.scripting_library.orders.order_tags as order_tags
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
        with mock.patch.object(create_order, "_paired_order_is_closed", mock.Mock(return_value=True)) \
             as _paired_order_is_closed_mock:
            assert [] == await create_order.create_order_instance(
                mock_context, "side", "symbol", "order_amount", "order_target_position",
                "order_type_name", "order_offset", "order_min_offset", "order_max_offset", "order_limit_offset",
                "slippage_limit", "time_limit", "reduce_only", "post_only", "one_cancels_the_other", "tag", "linked_to")
            _paired_order_is_closed_mock.assert_called_once_with(mock_context, "linked_to",
                                                                 "one_cancels_the_other", "tag")
            _get_order_quantity_and_side_mock.assert_not_called()
            _get_order_details_mock.assert_not_called()
            _create_order_mock.assert_not_called()
        with mock.patch.object(create_order, "_paired_order_is_closed", mock.Mock(return_value=False)) \
             as _paired_order_is_closed_mock:
            await create_order.create_order_instance(
                mock_context, "side", "symbol", "order_amount", "order_target_position",
                "order_type_name", "order_offset", "order_min_offset", "order_max_offset", "order_limit_offset",
                "slippage_limit", "time_limit", "reduce_only", "post_only", "one_cancels_the_other", "tag", "linked_to")
            _paired_order_is_closed_mock.assert_called_once_with(mock_context, "linked_to",
                                                                 "one_cancels_the_other", "tag")
            _get_order_quantity_and_side_mock.assert_called_once_with(mock_context, "order_amount",
                                                                      "order_target_position", "order_type_name",
                                                                      "side", "reduce_only")
            _get_order_details_mock.assert_called_once_with(mock_context, "order_type_name", "sell", "order_offset",
                                                            "reduce_only", "order_limit_offset")
            _create_order_mock.assert_called_once_with(mock_context, "symbol", decimal.Decimal(1), 2, "tag",
                                                       1, 3, "order_min_offset", 7, "linked_to",
                                                       "one_cancels_the_other")


def test_paired_order_is_closed(null_context):
    assert create_order._paired_order_is_closed(null_context, None, False, "tag") is False
    linked_to = mock.Mock()
    with mock.patch.object(linked_to, "is_closed", mock.Mock(return_value=True)) as is_closed_mock:
        assert create_order._paired_order_is_closed(null_context, [linked_to, linked_to], False, "tag") is True
        assert is_closed_mock.call_count == 2
    with mock.patch.object(linked_to, "is_closed", mock.Mock(return_value=False)) as is_closed_mock:
        assert create_order._paired_order_is_closed(null_context, linked_to, False, "tag") is False
        is_closed_mock.assert_called_once()

    order = mock.Mock()
    order.one_cancels_the_other = True
    order.tag = "other_tag"
    null_context.just_created_orders = []
    assert create_order._paired_order_is_closed(null_context, None, True, "tag") is False
    null_context.just_created_orders = [order]
    with mock.patch.object(order, "is_closed", mock.Mock(return_value=True)) as is_closed_mock:
        assert create_order._paired_order_is_closed(null_context, None, True, "tag") is False
        is_closed_mock.assert_not_called()
        order.tag = "tag"
        assert create_order._paired_order_is_closed(null_context, None, True, "tag") is True
        is_closed_mock.assert_called_once()


def test_use_total_holding():
    with mock.patch.object(create_order, "_is_stop_order", mock.Mock(return_value=False)) as _is_stop_order_mock:
        assert create_order._use_total_holding("type") is False
        _is_stop_order_mock.assert_called_once_with("type")
    with mock.patch.object(create_order, "_is_stop_order", mock.Mock(return_value=True)) as _is_stop_order_mock:
        assert create_order._use_total_holding("type2") is True
        _is_stop_order_mock.assert_called_once_with("type2")


def test_is_stop_order():
    assert create_order._is_stop_order("") is False
    assert create_order._is_stop_order("market") is False
    assert create_order._is_stop_order("limit") is False
    assert create_order._is_stop_order("stop_loss") is True
    assert create_order._is_stop_order("stop_market") is True
    assert create_order._is_stop_order("stop_limit") is True
    assert create_order._is_stop_order("trailing_stop_loss") is True
    assert create_order._is_stop_order("trailing_market") is False
    assert create_order._is_stop_order("trailing_limit") is False


async def test_get_order_quantity_and_side(null_context):
    # order_amount and order_target_position are both not set
    with pytest.raises(errors.InvalidArgumentError):
        await create_order._get_order_quantity_and_side(null_context, None, None, "", "", True)

    # order_amount and order_target_position are set
    with pytest.raises(errors.InvalidArgumentError):
        await create_order._get_order_quantity_and_side(null_context, 1, 2, "", "", True)

    # order_amount but no side
    with pytest.raises(errors.InvalidArgumentError):
        await create_order._get_order_quantity_and_side(null_context, 1, None, "", None, True)
    with pytest.raises(errors.InvalidArgumentError):
        await create_order._get_order_quantity_and_side(null_context, 1, None, "", "fsdsfds", True)

    with mock.patch.object(position_size, "get_amount",
                           mock.AsyncMock(return_value=decimal.Decimal(1))) as get_amount_mock:
        with mock.patch.object(create_order, "_use_total_holding",
                               mock.Mock(return_value=False)) as _use_total_holding_mock, \
                mock.patch.object(create_order, "_is_stop_order",
                                 mock.Mock(return_value=False)) as _is_stop_order_mock:
            assert await create_order._get_order_quantity_and_side(null_context, 1, None, "", "sell", True) \
                   == (decimal.Decimal(1), "sell")
            get_amount_mock.assert_called_once_with(null_context, 1, "sell", True, False, use_total_holding=False)
            get_amount_mock.reset_mock()
            _is_stop_order_mock.assert_called_once_with("")
            _use_total_holding_mock.assert_called_once_with("")
        with mock.patch.object(create_order, "_use_total_holding",
                               mock.Mock(return_value=True)) as _use_total_holding_mock, \
                mock.patch.object(create_order, "_is_stop_order",
                                 mock.Mock(return_value=True)) as _is_stop_order_mock:
            assert await create_order._get_order_quantity_and_side(null_context, 1, None, "order_type", "sell", False) \
                   == (decimal.Decimal(1), "sell")
            get_amount_mock.assert_called_once_with(null_context, 1, "sell", False, True, use_total_holding=True)
            get_amount_mock.reset_mock()
            _is_stop_order_mock.assert_called_once_with("order_type")
            _use_total_holding_mock.assert_called_once_with("order_type")

    with mock.patch.object(position_size, "get_target_position",
                           mock.AsyncMock(return_value=(decimal.Decimal(10), "buy"))) as get_target_position_mock:
        with mock.patch.object(create_order, "_use_total_holding",
                               mock.Mock(return_value=True)) as _use_total_holding_mock, \
             mock.patch.object(create_order, "_is_stop_order",
                               mock.Mock(return_value=False)) as _is_stop_order_mock:
            assert await create_order._get_order_quantity_and_side(null_context, None, 1, "order_type", None, True) \
                   == (decimal.Decimal(10), "buy")
            get_target_position_mock.assert_called_once_with(null_context, 1, True, False, use_total_holding=True)
            get_target_position_mock.reset_mock()
            _is_stop_order_mock.assert_called_once_with("order_type")
            _use_total_holding_mock.assert_called_once_with("order_type")
        with mock.patch.object(create_order, "_use_total_holding",
                               mock.Mock(return_value=False)) as _use_total_holding_mock, \
             mock.patch.object(create_order, "_is_stop_order",
                               mock.Mock(return_value=True)) as _is_stop_order_mock:
            assert await create_order._get_order_quantity_and_side(null_context, None, 1, "order_type", None, False) \
                   == (decimal.Decimal(10), "buy")
            get_target_position_mock.assert_called_once_with(null_context, 1, False, True, use_total_holding=False)
            get_target_position_mock.reset_mock()
            _is_stop_order_mock.assert_called_once_with("order_type")
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

        # without linked orders
        # don't plot orders
        mock_context.plot_orders = False
        orders = await create_order._create_order(
            mock_context, "BTC/USDT", decimal.Decimal(1), decimal.Decimal(100), "tag",
            trading_enums.TraderOrderType.BUY_MARKET, None, None, None, None, False)
        get_pre_order_data_mock.assert_called_once_with(mock_context.exchange_manager, symbol="BTC/USDT",
                                                        timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT)
        store_orders_mock.assert_not_called()
        assert len(orders) == 1
        assert isinstance(orders[0], trading_personal_data.BuyMarketOrder)
        assert orders[0].symbol == "BTC/USDT"
        assert orders[0].tag == "tag"
        assert orders[0].one_cancels_the_other is False
        assert orders[0].origin_price == decimal.Decimal(105)
        assert orders[0].origin_quantity == decimal.Decimal(1)
        assert mock_context.just_created_orders == orders
        mock_context.just_created_orders = []
        get_pre_order_data_mock.reset_mock()

        # with linked orders
        # plot orders
        mock_context.plot_orders = True
        linked_order = trading_personal_data.LimitOrder(mock_context.trader)
        orders = await create_order._create_order(
            mock_context, "BTC/USDT", decimal.Decimal(1), decimal.Decimal(100), "tag2",
            trading_enums.TraderOrderType.TRAILING_STOP,
            trading_enums.TradeOrderSide.BUY, decimal.Decimal(5), None,
            [linked_order], False)
        get_pre_order_data_mock.assert_called_once_with(mock_context.exchange_manager, symbol="BTC/USDT",
                                                        timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT)
        store_orders_mock.assert_called_once()
        assert store_orders_mock.mock_calls
        assert store_orders_mock.mock_calls[0].args[0] is mock_context
        assert orders is store_orders_mock.mock_calls[0].args[1]
        assert len(orders) == 1
        assert isinstance(orders[0], trading_personal_data.TrailingStopOrder)
        assert orders[0].symbol == "BTC/USDT"
        assert orders[0].tag == "tag2"
        assert orders[0].one_cancels_the_other is False
        assert orders[0].origin_price == decimal.Decimal(100)
        assert orders[0].origin_quantity == decimal.Decimal(1)
        assert orders[0].trader == mock_context.trader
        assert orders[0].trailing_percent == decimal.Decimal(5)
        assert orders[0].linked_to is linked_order
        assert mock_context.just_created_orders == orders
        mock_context.just_created_orders = []
        get_pre_order_data_mock.reset_mock()
        store_orders_mock.reset_mock()

        # with one_cancels_the_other and tag similar to previously created orders: links them together
        previous_orders = [trading_personal_data.LimitOrder(mock_context.trader),
                           trading_personal_data.LimitOrder(mock_context.trader)]
        previous_orders[0].one_cancels_the_other = True
        with mock.patch.object(create_order, "_pre_initialize_order_callback", mock.AsyncMock()) \
             as _pre_initialize_order_callback_mock:
            mock_context.plot_orders = False
            orders = await create_order._create_order(
                mock_context, "BTC/USDT", decimal.Decimal(1), decimal.Decimal(100), "tag2",
                trading_enums.TraderOrderType.TRAILING_STOP,
                trading_enums.TradeOrderSide.BUY, decimal.Decimal(5), None,
                None, True)
            get_pre_order_data_mock.assert_called_once_with(mock_context.exchange_manager, symbol="BTC/USDT",
                                                            timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT)
            store_orders_mock.assert_not_called()
            assert len(orders) == 1
            assert isinstance(orders[0], trading_personal_data.TrailingStopOrder)
            assert orders[0].symbol == "BTC/USDT"
            assert orders[0].tag == "tag2"
            assert orders[0].one_cancels_the_other is True
            assert orders[0].origin_price == decimal.Decimal(100)
            assert orders[0].origin_quantity == decimal.Decimal(1)
            assert orders[0].trader == mock_context.trader
            assert orders[0].trailing_percent == decimal.Decimal(5)
            assert mock_context.just_created_orders == orders
            mock_context.just_created_orders = []

            _pre_initialize_order_callback_mock.assert_called_once_with(orders[0])


async def test_pre_initialize_order_callback():
    order = mock.Mock()
    order.symbol = "symbol"
    order.tag = "tag"
    order.add_linked_order = mock.Mock()

    order_2 = mock.Mock()
    order_2.one_cancels_the_other = False
    order.add_linked_order = mock.Mock()

    order_3 = mock.Mock()
    order_3.one_cancels_the_other = True
    order.add_linked_order = mock.Mock()

    order_4 = mock.Mock()
    order_4.one_cancels_the_other = True
    order.add_linked_order = mock.Mock()

    order.trader = mock.Mock()
    order.trader.exchange_manager = mock.Mock()
    order.trader.exchange_manager.exchange_personal_data = mock.Mock()
    order.trader.exchange_manager.exchange_personal_data.orders_manager = mock.Mock()
    order.trader.exchange_manager.exchange_personal_data.orders_manager.get_open_orders = \
        mock.Mock(return_value=[order, order_2, order_3, order_4])

    await create_order._pre_initialize_order_callback(order)
    order.trader.exchange_manager.exchange_personal_data.orders_manager.get_open_orders.\
        assert_called_once_with(symbol="symbol", tag="tag")
    order_2.add_linked_order.assert_not_called()
    order_3.add_linked_order.assert_called_once_with(order)
    order_4.add_linked_order.assert_called_once_with(order)
    assert order.add_linked_order.mock_calls[0].args == (order_3, )
    assert order.add_linked_order.mock_calls[1].args == (order_4, )
