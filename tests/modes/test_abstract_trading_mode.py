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
import mock

# prevent circular import
import octobot_trading.api
import octobot_trading.modes as modes
import octobot_trading.signals as signals
import octobot_trading.constants as constants
import octobot_commons.constants as common_constants
import octobot_commons.errors as common_errors
import octobot_commons.signals.signals_emitter as signals_emitter

from tests import event_loop
from tests.exchanges import simulated_exchange_manager, simulated_trader
from tests.personal_data.orders import buy_limit_order


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


@pytest.fixture
def trading_mode(simulated_trader):
    config, exchange_manager_inst, trader_inst = simulated_trader
    mode = modes.AbstractTradingMode(config, exchange_manager_inst)
    exchange_manager_inst.trading_modes = [mode]
    mode.trading_config = {}
    return mode


async def test_remote_signal_publisher(trading_mode):
    with mock.patch.object(trading_mode, "should_emit_trading_signal", mock.Mock(return_value=False)) \
         as should_emit_trading_signal_mock:
        async with trading_mode.remote_signal_publisher("BTC/USDT") as builder:
            should_emit_trading_signal_mock.assert_called_once()
            assert builder is None
    with mock.patch.object(trading_mode, "should_emit_trading_signal", mock.Mock(return_value=True)) \
         as should_emit_trading_signal_mock:
        async with trading_mode.remote_signal_publisher("BTC/USDT") as builder:
            should_emit_trading_signal_mock.assert_called_once()
            assert builder.identifier == trading_mode.get_name()
            assert isinstance(builder, signals.TradingSignalBundleBuilder)
        should_emit_trading_signal_mock.reset_mock()
        trading_mode.trading_config = {
            common_constants.CONFIG_TRADING_SIGNALS_STRATEGY: "hello identifier"
        }
        async with trading_mode.remote_signal_publisher("BTC/USDT") as builder:
            should_emit_trading_signal_mock.assert_called_once()
            assert builder.identifier == "hello identifier"
            assert isinstance(builder, signals.TradingSignalBundleBuilder)
            assert builder.strategy == trading_mode.get_name()


async def test_create_order(trading_mode, buy_limit_order):
    octobot_trading.api.force_set_mark_price(trading_mode.exchange_manager, "BTC/USDT", 1000)
    buy_limit_order.origin_quantity = decimal.Decimal("0.1")
    buy_limit_order.symbol = "BTC/USDT"
    trading_mode.exchange_manager.trader = mock.Mock(create_order=mock.AsyncMock(return_value=buy_limit_order))
    create_order_mock = trading_mode.exchange_manager.trader.create_order
    # without context manager
    with mock.patch.object(trading_mode, "should_emit_trading_signal", mock.Mock(return_value=False)) \
         as should_emit_trading_signal_mock:
        assert await trading_mode.create_order(buy_limit_order, loaded=False, params=None, pre_init_callback=None) \
               is buy_limit_order
        assert should_emit_trading_signal_mock.call_count == 1
        create_order_mock.assert_called_once_with(
            buy_limit_order, loaded=False, params=None, pre_init_callback=None
        )
        create_order_mock.reset_mock()
        should_emit_trading_signal_mock.reset_mock()
    with mock.patch.object(trading_mode, "should_emit_trading_signal", mock.Mock(return_value=True)) \
         as should_emit_trading_signal_mock:
        with pytest.raises(common_errors.MissingSignalBuilder):
            await trading_mode.create_order(buy_limit_order, loaded=False, params=None, pre_init_callback=None)
        assert should_emit_trading_signal_mock.call_count == 1
        create_order_mock.assert_called_once_with(
            buy_limit_order, loaded=False, params=None, pre_init_callback=None
        )
        # created order but failed to register signal
        create_order_mock.reset_mock()
        should_emit_trading_signal_mock.reset_mock()
    # with context manager
    with mock.patch.object(signals_emitter, "emit_signal_bundle", mock.AsyncMock()) as emit_signal_bundle_mock:
        with mock.patch.object(trading_mode, "should_emit_trading_signal", mock.Mock(return_value=False)) \
                as should_emit_trading_signal_mock:
            async with trading_mode.remote_signal_publisher("BTC/USDT") as builder:
                assert await trading_mode.create_order(buy_limit_order, loaded=False,
                                                       params=None, pre_init_callback=None) \
                       is buy_limit_order
                assert builder is None
                assert should_emit_trading_signal_mock.call_count == 2
                create_order_mock.assert_called_once_with(
                    buy_limit_order, loaded=False, params=None, pre_init_callback=None
                )
                create_order_mock.reset_mock()
                should_emit_trading_signal_mock.reset_mock()
            emit_signal_bundle_mock.assert_not_called()
        with mock.patch.object(trading_mode, "should_emit_trading_signal", mock.Mock(return_value=True)) \
                as should_emit_trading_signal_mock:
            async with trading_mode.remote_signal_publisher("BTC/USDT") as builder:
                assert await trading_mode.create_order(buy_limit_order, loaded=False, params=None,
                                                       pre_init_callback=None) \
                       is buy_limit_order
                assert not builder.is_empty()
                assert should_emit_trading_signal_mock.call_count == 2
                create_order_mock.assert_called_once_with(
                    buy_limit_order, loaded=False, params=None, pre_init_callback=None
                )
                # created order but failed to register signal
                create_order_mock.reset_mock()
                should_emit_trading_signal_mock.reset_mock()
            emit_signal_bundle_mock.assert_called_once()


async def test_cancel_order(trading_mode, buy_limit_order):
    buy_limit_order.symbol = "BTC/USDT"
    trading_mode.exchange_manager.trader = mock.Mock(cancel_order=mock.AsyncMock(return_value=True))
    cancel_order_mock = trading_mode.exchange_manager.trader.cancel_order
    # without context manager
    with mock.patch.object(trading_mode, "should_emit_trading_signal", mock.Mock(return_value=True)) \
            as should_emit_trading_signal_mock:
        with pytest.raises(common_errors.MissingSignalBuilder):
            await trading_mode.cancel_order(buy_limit_order, ignored_order="ignored")
        should_emit_trading_signal_mock.assert_called_once()
        cancel_order_mock.assert_called_once_with(
            buy_limit_order, ignored_order="ignored", wait_for_cancelling=True,
            cancelling_timeout=constants.INDIVIDUAL_ORDER_SYNC_TIMEOUT
        )
        should_emit_trading_signal_mock.reset_mock()
        cancel_order_mock.reset_mock()
    with mock.patch.object(trading_mode, "should_emit_trading_signal", mock.Mock(return_value=False)) \
            as should_emit_trading_signal_mock:
        assert await trading_mode.cancel_order(buy_limit_order, ignored_order="ignored") is True
        should_emit_trading_signal_mock.assert_called_once()
        cancel_order_mock.assert_called_once_with(
            buy_limit_order, ignored_order="ignored", wait_for_cancelling=True,
            cancelling_timeout=constants.INDIVIDUAL_ORDER_SYNC_TIMEOUT
        )
        should_emit_trading_signal_mock.reset_mock()
        cancel_order_mock.reset_mock()
    # with context manager
    with mock.patch.object(signals_emitter, "emit_signal_bundle", mock.AsyncMock()) as emit_signal_bundle_mock:
        with mock.patch.object(trading_mode, "should_emit_trading_signal", mock.Mock(return_value=True)) \
                as should_emit_trading_signal_mock:
            async with trading_mode.remote_signal_publisher("BTC/USDT"):
                assert await trading_mode.cancel_order(buy_limit_order, ignored_order="ignored") is True
                assert should_emit_trading_signal_mock.call_count == 2
                cancel_order_mock.assert_called_once_with(
                    buy_limit_order, ignored_order="ignored", wait_for_cancelling=True,
                    cancelling_timeout=constants.INDIVIDUAL_ORDER_SYNC_TIMEOUT
                )
                should_emit_trading_signal_mock.reset_mock()
                cancel_order_mock.reset_mock()
        emit_signal_bundle_mock.assert_called_once()
        emit_signal_bundle_mock.reset_mock()
        with mock.patch.object(trading_mode, "should_emit_trading_signal", mock.Mock(return_value=False)) \
                as should_emit_trading_signal_mock:
            async with trading_mode.remote_signal_publisher("BTC/USDT"):
                assert await trading_mode.cancel_order(buy_limit_order, ignored_order="ignored") is True
                assert should_emit_trading_signal_mock.call_count == 2
                cancel_order_mock.assert_called_once_with(
                    buy_limit_order, ignored_order="ignored", wait_for_cancelling=True,
                    cancelling_timeout=constants.INDIVIDUAL_ORDER_SYNC_TIMEOUT
                )
                should_emit_trading_signal_mock.reset_mock()
                cancel_order_mock.reset_mock()
        emit_signal_bundle_mock.assert_not_called()


async def test_edit_order(trading_mode, buy_limit_order):
    buy_limit_order.symbol = "BTC/USDT"
    trading_mode.exchange_manager.trader = mock.Mock(edit_order=mock.AsyncMock(return_value=True))
    edit_order_mock = trading_mode.exchange_manager.trader.edit_order
    # without context manager
    with mock.patch.object(trading_mode, "should_emit_trading_signal", mock.Mock(return_value=True)) \
            as should_emit_trading_signal_mock:
        with pytest.raises(common_errors.MissingSignalBuilder):
            await trading_mode.edit_order(buy_limit_order, edited_quantity=constants.ONE, edited_price=constants.ONE,
                                          edited_stop_price=constants.ONE, edited_current_price=constants.ONE,
                                          params=None)
        should_emit_trading_signal_mock.assert_called_once()
        edit_order_mock.assert_called_once_with(
            buy_limit_order, edited_quantity=constants.ONE, edited_price=constants.ONE,
            edited_stop_price=constants.ONE, edited_current_price=constants.ONE,
            params=None)
        should_emit_trading_signal_mock.reset_mock()
        edit_order_mock.reset_mock()
    with mock.patch.object(trading_mode, "should_emit_trading_signal", mock.Mock(return_value=False)) \
            as should_emit_trading_signal_mock:
        assert await trading_mode.edit_order(buy_limit_order, edited_quantity=constants.ONE, edited_price=constants.ONE,
                                             edited_stop_price=constants.ONE, edited_current_price=constants.ONE,
                                             params=None) is True
        should_emit_trading_signal_mock.assert_called_once()
        edit_order_mock.assert_called_once_with(
            buy_limit_order, edited_quantity=constants.ONE, edited_price=constants.ONE,
            edited_stop_price=constants.ONE, edited_current_price=constants.ONE,
            params=None)
        should_emit_trading_signal_mock.reset_mock()
        edit_order_mock.reset_mock()
    # with context manager
    with mock.patch.object(signals_emitter, "emit_signal_bundle", mock.AsyncMock()) as emit_signal_bundle_mock:
        with mock.patch.object(trading_mode, "should_emit_trading_signal", mock.Mock(return_value=True)) \
                as should_emit_trading_signal_mock:
            async with trading_mode.remote_signal_publisher("BTC/USDT"):
                assert await trading_mode.edit_order(buy_limit_order, edited_quantity=constants.ONE,
                                                     edited_price=constants.ONE, edited_stop_price=constants.ONE,
                                                     edited_current_price=constants.ONE, params=None) is True
                assert should_emit_trading_signal_mock.call_count == 2
                edit_order_mock.assert_called_once_with(
                    buy_limit_order, edited_quantity=constants.ONE, edited_price=constants.ONE,
                    edited_stop_price=constants.ONE, edited_current_price=constants.ONE,
                    params=None)
                should_emit_trading_signal_mock.reset_mock()
                edit_order_mock.reset_mock()
        emit_signal_bundle_mock.assert_called_once()
        emit_signal_bundle_mock.reset_mock()
        with mock.patch.object(trading_mode, "should_emit_trading_signal", mock.Mock(return_value=False)) \
                as should_emit_trading_signal_mock:
            async with trading_mode.remote_signal_publisher("BTC/USDT"):
                assert await trading_mode.edit_order(buy_limit_order, edited_quantity=constants.ONE,
                                                     edited_price=constants.ONE, edited_stop_price=constants.ONE,
                                                     edited_current_price=constants.ONE, params=None) is True
                assert should_emit_trading_signal_mock.call_count == 2
                edit_order_mock.assert_called_once_with(
                    buy_limit_order, edited_quantity=constants.ONE, edited_price=constants.ONE,
                    edited_stop_price=constants.ONE, edited_current_price=constants.ONE,
                    params=None)
                should_emit_trading_signal_mock.reset_mock()
                edit_order_mock.reset_mock()
        emit_signal_bundle_mock.assert_not_called()
