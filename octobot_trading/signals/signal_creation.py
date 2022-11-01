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
import contextlib

import octobot_trading.modes.script_keywords as script_keywords
import octobot_trading.personal_data.orders as orders
import octobot_trading.signals.trading_signal_bundle_builder as trading_signal_bundle_builder

import octobot_commons.logging as logging
import octobot_commons.signals as signals
import octobot_commons.errors as commons_errors
import octobot_commons.authentication as authentication


@contextlib.asynccontextmanager
async def remote_signal_publisher(exchange_manager, symbol: str, emit_trading_signals: bool):
    try:
        if emit_trading_signals:
            try:
                trading_mode = exchange_manager.trading_modes[0]
            except IndexError:
                yield None
                return
            try:
                async with signals.SignalPublisher.instance().remote_signal_bundle_builder(
                    symbol,
                    trading_mode.get_trading_signal_identifier(),
                    trading_mode.TRADING_SIGNAL_TIMEOUT,
                    trading_signal_bundle_builder.TradingSignalBundleBuilder,
                    (trading_mode.get_name(),)
                ) as signal_builder:
                    yield signal_builder
            except (authentication.AuthenticationRequired, authentication.UnavailableError) as e:
                logging.get_logger(__name__).exception(e, True, f"Failed to send trading signals: {e}")
        else:
            yield None
    except commons_errors.MissingSignalBuilder as e:
        logging.get_logger(__name__).exception(e, True, f"Error when sending trading signal: no signal builder {e}")


def should_emit_trading_signal(exchange_manager):
    try:
        return exchange_manager.trading_modes[0].should_emit_trading_signal()
    except IndexError:
        return False


async def create_order(exchange_manager, should_emit_signal, order,
                       loaded: bool = False, params: dict = None, pre_init_callback=None):
    order_pf_percent = f"0{script_keywords.QuantityType.PERCENT.value}"
    if should_emit_signal:
        percent = await orders.get_order_size_portfolio_percent(
            exchange_manager,
            order.origin_quantity,
            order.side,
            order.symbol
        )
        order_pf_percent = f"{float(percent)}{script_keywords.QuantityType.PERCENT.value}"
    created_order = await exchange_manager.trader.create_order(
        order, loaded=loaded, params=params, pre_init_callback=pre_init_callback
    )
    if created_order is not None and should_emit_signal:
        signals.SignalPublisher.instance().get_signal_bundle_builder(order.symbol).add_created_order(
            created_order, exchange_manager, target_amount=order_pf_percent
        )
    return created_order


async def cancel_order(exchange_manager, should_emit_signal, order, ignored_order: object = None) -> bool:
    cancelled = await exchange_manager.trader.cancel_order(order, ignored_order=ignored_order)
    if should_emit_signal and cancelled:
        signals.SignalPublisher.instance().get_signal_bundle_builder(order.symbol).add_cancelled_order(
            order, exchange_manager
        )
    return cancelled


async def edit_order(
    exchange_manager,
    should_emit_signal,
    order,
    edited_quantity: decimal.Decimal = None,
    edited_price: decimal.Decimal = None,
    edited_stop_price: decimal.Decimal = None,
    edited_current_price: decimal.Decimal = None,
    params: dict = None
) -> bool:
    changed = await exchange_manager.trader.edit_order(
        order,
        edited_quantity=edited_quantity,
        edited_price=edited_price,
        edited_stop_price=edited_stop_price,
        edited_current_price=edited_current_price,
        params=params
    )
    if should_emit_signal and changed:
        signals.SignalPublisher.instance().get_signal_bundle_builder(order.symbol).add_edited_order(
            order,
            exchange_manager,
            updated_target_amount=edited_quantity,
            updated_limit_price=edited_price,
            updated_stop_price=edited_stop_price,
            updated_current_price=edited_current_price,
        )
    return changed
